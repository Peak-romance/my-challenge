# -*- coding: utf-8 -*-
"""
路由：资产二维码（交互增强 · 扫码认领）
------------------------------------------------------------------
设计要点：
  - 接口**免登录公开**：仅把"资产详情深链"编码进二维码，本身不含任何敏感数据；
    扫码后打开的 /user/asset.html 仍需登录，因此无越权风险。
  - 前端用 <img src> 直接展示，避免带 JWT 的图片鉴权问题。
  - base 缺省取请求 base_url；管理端标签打印页会传入 location.origin，
    以便二维码指向手机可访问的局域网地址（跨设备扫码）。
依赖页面：frontend/user/asset.html（查看/下载二维码）、
         frontend/admin/labels.html（批量打印资产二维码标签）
"""
import io
import urllib.parse

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response

from ..database import get_db
from ..models import Asset
from sqlalchemy.orm import Session

try:
    import segno
except ImportError:  # pragma: no cover
    segno = None


def build_qr_target(asset_id: int, base: str = "") -> str:
    """构造二维码指向的深链：<base>/user/asset.html?id=<asset_id>"""
    base = (base or "").strip().rstrip("/")
    return f"{base}/user/asset.html?id={asset_id}"


router = APIRouter(tags=["二维码"])


@router.get("/api/assets/{asset_id}/qrcode")
def asset_qrcode(
    asset_id: int,
    request: Request,
    base: str = Query("", description="可选：二维码指向的基础地址，如 http://192.168.1.10:3000"),
    size: int = Query(8, ge=2, le=40, description="二维码模块缩放，数值越大越清晰"),
    db: Session = Depends(get_db),
):
    """
    生成资产二维码（PNG）。扫码后打开资产详情页，登录即可认领 / 查看流转。
    说明：为满足前端 <img> 免鉴权展示，接口本身不依赖返回内容做权限控制，
    仅编码一个指向登录页的深链；真实数据仍由详情页的登录守卫保护。
    """
    if segno is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=503, detail="二维码生成依赖（segno）未安装")

    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if asset is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="物资不存在")

    # base 可能由前端 URL 编码后传入，先解码
    if base:
        try:
            base = urllib.parse.unquote(base)
        except Exception:
            pass
    if not base:
        base = str(request.base_url).rstrip("/")

    target = build_qr_target(asset.id, base)
    buf = io.BytesIO()
    qr = segno.make(target, error="m")
    qr.save(buf, kind="png", scale=size, border=2, dark="#1f2937", light="#ffffff")
    buf.seek(0)
    return Response(content=buf.getvalue(), media_type="image/png")
