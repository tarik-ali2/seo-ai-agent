import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import get_db
import models
import auth as auth_utils

router = APIRouter(prefix="/api/reports", tags=["reports"])

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")


def _get_report_dir(audit_id: int) -> str:
    return os.path.join(REPORTS_DIR, str(audit_id))


@router.get("/{audit_id}/download")
def download_zip(
    audit_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    audit = db.query(models.Audit).filter(
        models.Audit.id == audit_id,
        models.Audit.user_id == current_user.id,
    ).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    if audit.status != "completed":
        raise HTTPException(status_code=400, detail="Audit is not completed yet")

    zip_path = os.path.join(_get_report_dir(audit_id), "SEO_Audit_Reports.zip")
    if not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="Report files not found — re-run the audit")

    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename=f"SEO_Audit_{audit_id}.zip",
        headers={"Content-Disposition": f'attachment; filename="SEO_Audit_{audit_id}.zip"'},
    )


@router.get("/{audit_id}/files")
def list_report_files(
    audit_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    audit = db.query(models.Audit).filter(
        models.Audit.id == audit_id,
        models.Audit.user_id == current_user.id,
    ).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    report_dir = _get_report_dir(audit_id)
    if not os.path.exists(report_dir):
        return {"files": []}

    files = []
    for fname in sorted(os.listdir(report_dir)):
        if fname.endswith(".docx"):
            fpath = os.path.join(report_dir, fname)
            files.append({
                "name": fname,
                "size_kb": round(os.path.getsize(fpath) / 1024, 1),
                "download_url": f"/api/reports/{audit_id}/file/{fname}",
            })
    return {"files": files}


@router.get("/{audit_id}/file/{filename}")
def download_single_file(
    audit_id: int,
    filename: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    audit = db.query(models.Audit).filter(
        models.Audit.id == audit_id,
        models.Audit.user_id == current_user.id,
    ).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    # Prevent path traversal
    safe_name = os.path.basename(filename)
    if not safe_name.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files can be downloaded")

    file_path = os.path.join(_get_report_dir(audit_id), safe_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=safe_name,
    )
