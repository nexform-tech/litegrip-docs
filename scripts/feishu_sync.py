#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把仓库里的 PDF 同步到飞书文档里对应的「文件块」。

飞书文档中的 PDF 是一个文件块，换内容不能原地覆盖，要拆成三步：把新文件传成
媒体 token、再把这个 token 绑回原来的块。块本身不重建，所以文档里的位置、协
作者权限和分享链接都不会变。

块按文件名匹配（见 scripts/feishu_sync.json）。找不到就报错退出，不自动新建，
免得每次跑完多出一个重复的 PDF。

配置里的字符串项表示仓库根目录下同名文件；仓库路径与飞书展示名不一致时，用
{"path": "drawings/xxx.pdf", "name": "图纸.pdf"} 的形式。

用法：
    FEISHU_APP_ID=... FEISHU_APP_SECRET=... python3 scripts/feishu_sync.py

应用需要先被文档所有者加成「可编辑」的文档协作者：
文档右上角「…」→「…更多」→「添加文档应用」。
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "scripts", "feishu_sync.json")
BASE = "https://open.feishu.cn/open-apis"
# 这些 PDF 都远小于单次上传上限（20 MB），无需分片。
MAX_SINGLE_UPLOAD = 20 * 1024 * 1024


def api(method, path, body=None, token=None, timeout=60):
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(BASE + path, data=data, method=method)
    if token:
        req.add_header("Authorization", "Bearer " + token)
    if data is not None:
        req.add_header("Content-Type", "application/json; charset=utf-8")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        raise SystemExit(f"{method} {path} 失败：HTTP {exc.code} {body}") from exc


def tenant_token(app_id, app_secret):
    result = api(
        "POST",
        "/auth/v3/tenant_access_token/internal",
        {"app_id": app_id, "app_secret": app_secret},
    )
    if result.get("code") != 0:
        raise SystemExit(f"取 tenant_access_token 失败：{result.get('msg')}")
    return result["tenant_access_token"]


def list_blocks(token, document_id):
    blocks = []
    page_token = ""
    while True:
        path = f"/docx/v1/documents/{document_id}/blocks?page_size=500"
        if page_token:
            path += "&page_token=" + urllib.parse.quote(page_token)
        result = api("GET", path, token=token)
        if result.get("code") != 0:
            raise SystemExit(f"读文档块失败：{result.get('msg')}")
        data = result["data"]
        blocks.extend(data.get("items") or [])
        page_token = data.get("page_token") or ""
        if not data.get("has_more"):
            return blocks


def find_file_block(blocks, name):
    """返回名字匹配的文件块 ID；没有就返回 None。

    文件块在 API 里可能出现两层（外层 view 块 + 内层 file 块），两层的
    file.name 都可能是空的，只有真正挂文件的那层带名字，所以按名字找即可。
    """
    for block in blocks:
        file_info = block.get("file") or {}
        if block.get("block_type") == 23 and file_info.get("name") == name:
            return block["block_id"]
    return None


def file_entry(entry):
    """把配置项统一成 (仓库里的相对路径, 飞书文档里的文件名)。

    字符串项表示两者相同；对象项用于仓库文件名与飞书里的展示名不一致的情况。
    """
    if isinstance(entry, str):
        return entry, entry
    return entry["path"], entry["name"]


def encode_multipart(fields, file_name, file_bytes):
    """拼 multipart/form-data 请求体。

    Content-Disposition 里的 filename 用 ASCII，中文名由 file_name 字段传给
    飞书，避免 http.client 按 latin-1 编码请求头时报错。
    """
    boundary = "----feishu" + uuid.uuid4().hex
    chunks = []
    for key, value in fields.items():
        chunks.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode(
                "utf-8"
            )
        )
    chunks.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="upload.pdf"\r\n'
        f"Content-Type: application/pdf\r\n\r\n".encode("utf-8")
    )
    chunks.append(file_bytes)
    chunks.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))
    return boundary, b"".join(chunks)


def upload_media(token, document_id, block_id, path, name):
    """上传文件到媒体库；name 是飞书文件块里显示的名字（也是同步脚本匹配用的键）。"""
    size = os.path.getsize(path)
    if size > MAX_SINGLE_UPLOAD:
        raise SystemExit(f"{name} 超过 20 MB，需要分片上传，脚本暂不支持")
    with open(path, "rb") as f:
        content = f.read()
    boundary, body = encode_multipart(
        {
            "file_name": name,
            "parent_type": "docx_file",
            "parent_node": block_id,
            "size": str(size),
            "extra": json.dumps({"drive_route_token": document_id}),
        },
        name,
        content,
    )
    req = urllib.request.Request(BASE + "/drive/v1/medias/upload_all", data=body, method="POST")
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Content-Type", "multipart/form-data; boundary=" + boundary)
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise SystemExit(
            f"上传 {name} 失败：HTTP {exc.code} "
            f"{exc.read().decode('utf-8', 'replace')}"
        ) from exc
    if result.get("code") != 0:
        raise SystemExit(f"上传 {name} 失败：{result.get('msg')}")
    return result["data"]["file_token"]


def replace_file(token, document_id, block_id, file_token):
    result = api(
        "PATCH",
        f"/docx/v1/documents/{document_id}/blocks/batch_update",
        {"requests": [{"block_id": block_id, "replace_file": {"token": file_token}}]},
        token=token,
    )
    if result.get("code") != 0:
        raise SystemExit(f"绑定文件块失败：{result.get('msg')}")


def main():
    app_id = os.environ.get("FEISHU_APP_ID", "").strip()
    app_secret = os.environ.get("FEISHU_APP_SECRET", "").strip()
    if not app_id or not app_secret:
        raise SystemExit("缺少 FEISHU_APP_ID / FEISHU_APP_SECRET 环境变量")

    with open(CONFIG, encoding="utf-8") as f:
        config = json.load(f)

    token = tenant_token(app_id, app_secret)
    for doc in config["documents"]:
        document_id = doc["document_id"]
        blocks = list_blocks(token, document_id)
        for entry in doc["files"]:
            rel_path, name = file_entry(entry)
            path = os.path.join(ROOT, rel_path)
            if not os.path.isfile(path):
                raise SystemExit(f"仓库里找不到 {rel_path}")
            block_id = find_file_block(blocks, name)
            if not block_id:
                raise SystemExit(
                    f"文档 {document_id} 里没有名为 {name} 的文件块；"
                    "先在飞书文档里建一个同名文件块，或检查 scripts/feishu_sync.json"
                )
            file_token = upload_media(token, document_id, block_id, path, name)
            replace_file(token, document_id, block_id, file_token)
            print(f"已同步 {name} -> {document_id}/{block_id}")


if __name__ == "__main__":
    main()
