"""Admin management functions for the ToVéCo voting platform."""

import csv
import io
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import aiofiles
from PIL import Image
from sqlalchemy.exc import SQLAlchemyError

from .config import settings
from .database import DatabaseManager
from .models import VoteRecord

logger = logging.getLogger(__name__)


class AdminManager:
    """Manages admin operations for logos, votes, and system maintenance."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize admin manager."""
        self.db_manager = db_manager

    # Logo Management Methods
    async def upload_logo(
        self, file_content: bytes, filename: str, new_name: str | None = None
    ) -> dict[str, Any]:
        """
        Upload and validate a new logo file.
        Returns operation result with success status and details.
        """
        try:
            # Validate file size
            file_size_mb = len(file_content) / (1024 * 1024)
            if file_size_mb > settings.MAX_UPLOAD_SIZE_MB:
                return {
                    "success": False,
                    "message": f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB}MB",
                    "file_size": f"{file_size_mb:.2f}MB",
                }

            # Validate file format using PIL
            try:
                image = Image.open(io.BytesIO(file_content))
                if image.format != "PNG":
                    return {
                        "success": False,
                        "message": "Only PNG files are allowed",
                        "detected_format": image.format,
                    }

                # Get image dimensions
                width, height = image.size
                logger.info(f"Image dimensions: {width}x{height}")

            except Exception as e:
                return {
                    "success": False,
                    "message": "Invalid or corrupted image file",
                    "error": str(e),
                }

            # Determine final filename
            if new_name:
                if not new_name.startswith("toveco") or not new_name.endswith(".png"):
                    return {
                        "success": False,
                        "message": "Filename must start with 'toveco' and end with '.png'",
                    }
                final_filename = new_name
            else:
                # Use original filename if it follows convention
                if not filename.startswith("toveco") or not filename.endswith(".png"):
                    return {
                        "success": False,
                        "message": "Original filename must start with 'toveco' and end with '.png'",
                    }
                final_filename = filename

            # Check if file already exists
            logo_path = settings.LOGOS_DIR / final_filename
            if logo_path.exists():
                return {
                    "success": False,
                    "message": f"Logo '{final_filename}' already exists",
                }

            # Save the file
            async with aiofiles.open(logo_path, "wb") as f:
                await f.write(file_content)

            logger.info(f"Logo uploaded successfully: {final_filename}")
            return {
                "success": True,
                "message": f"Logo '{final_filename}' uploaded successfully",
                "filename": final_filename,
                "size": f"{file_size_mb:.2f}MB",
                "dimensions": f"{width}x{height}",
            }

        except Exception as e:
            logger.error(f"Logo upload error: {e}")
            return {
                "success": False,
                "message": "Upload failed due to server error",
                "error": str(e),
            }

    def delete_logos(self, logo_names: list[str]) -> dict[str, Any]:
        """
        Delete multiple logo files.
        Returns operation result with success/failure details.
        """
        results: dict[str, Any] = {
            "success": True,
            "deleted": [],
            "failed": [],
            "message": "",
        }

        for logo_name in logo_names:
            try:
                logo_path = settings.LOGOS_DIR / logo_name

                if not logo_path.exists():
                    results["failed"].append(
                        {"filename": logo_name, "error": "File does not exist"}
                    )
                    continue

                # Security check - ensure file is in logos directory
                if not str(logo_path).startswith(str(settings.LOGOS_DIR)):
                    results["failed"].append(
                        {"filename": logo_name, "error": "Invalid file path"}
                    )
                    continue

                logo_path.unlink()
                results["deleted"].append(logo_name)
                logger.info(f"Deleted logo: {logo_name}")

            except Exception as e:
                logger.error(f"Failed to delete logo {logo_name}: {e}")
                results["failed"].append({"filename": logo_name, "error": str(e)})

        # Update overall success status
        if results["failed"]:
            results["success"] = len(results["deleted"]) > 0
            results["message"] = (
                f"Deleted {len(results['deleted'])}, failed {len(results['failed'])}"
            )
        else:
            results["message"] = f"Successfully deleted {len(results['deleted'])} logos"

        return results

    def rename_logo(self, old_name: str, new_name: str) -> dict[str, Any]:
        """
        Rename a logo file.
        Returns operation result.
        """
        try:
            # Validate new name
            if not new_name.startswith("toveco") or not new_name.endswith(".png"):
                return {
                    "success": False,
                    "message": "New filename must start with 'toveco' and end with '.png'",
                }

            old_path = settings.LOGOS_DIR / old_name
            new_path = settings.LOGOS_DIR / new_name

            if not old_path.exists():
                return {
                    "success": False,
                    "message": f"Logo '{old_name}' does not exist",
                }

            if new_path.exists():
                return {
                    "success": False,
                    "message": f"Logo '{new_name}' already exists",
                }

            old_path.rename(new_path)
            logger.info(f"Renamed logo: {old_name} -> {new_name}")

            return {
                "success": True,
                "message": f"Logo renamed from '{old_name}' to '{new_name}'",
                "old_name": old_name,
                "new_name": new_name,
            }

        except Exception as e:
            logger.error(f"Failed to rename logo {old_name}: {e}")
            return {
                "success": False,
                "message": "Rename failed due to server error",
                "error": str(e),
            }

    def get_logo_details(self) -> list[dict[str, Any]]:
        """Get detailed information about all logos."""
        logos = []

        for logo_path in settings.LOGOS_DIR.glob("toveco*.png"):
            try:
                stat = logo_path.stat()

                # Get image dimensions
                try:
                    with Image.open(logo_path) as img:
                        width, height = img.size
                        dimensions = f"{width}x{height}"
                except Exception:
                    dimensions = "Unknown"

                logos.append(
                    {
                        "filename": logo_path.name,
                        "size": stat.st_size,
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "modified": datetime.fromtimestamp(stat.st_mtime),
                        "dimensions": dimensions,
                    }
                )

            except Exception as e:
                logger.error(f"Error getting logo details for {logo_path.name}: {e}")

        return sorted(logos, key=lambda x: x["filename"])

    # Vote Management Methods
    def delete_single_vote(self, vote_id: int) -> dict[str, Any]:
        """
        Delete a single vote by its ID.
        Returns operation result.
        """
        try:
            success = self.db_manager.delete_vote_by_id(vote_id)

            if success:
                logger.info(f"Vote {vote_id} deleted by admin")
                return {
                    "success": True,
                    "message": f"Vote {vote_id} successfully deleted",
                }
            else:
                return {"success": False, "message": f"Vote {vote_id} not found"}

        except Exception as e:
            logger.error(f"Failed to delete vote {vote_id}: {e}")
            return {"success": False, "message": f"Failed to delete vote: {str(e)}"}

    def reset_all_votes(self) -> dict[str, Any]:
        """
        Reset all votes in the database.
        Returns operation result.
        """
        try:
            with self.db_manager.get_session() as session:
                vote_count = session.query(VoteRecord).count()
                session.query(VoteRecord).delete()
                session.commit()

            logger.warning(f"Reset {vote_count} votes from database")
            return {
                "success": True,
                "message": f"Successfully reset {vote_count} votes",
                "deleted_count": vote_count,
            }

        except SQLAlchemyError as e:
            logger.error(f"Failed to reset votes: {e}")
            return {
                "success": False,
                "message": "Failed to reset votes due to database error",
                "error": str(e),
            }

    def export_votes(self, format: str = "csv") -> dict[str, Any]:
        """
        Export votes in specified format (csv or json).
        Returns operation result with data or file path.
        """
        try:
            votes = self.db_manager.get_all_votes()

            if format.lower() == "csv":
                # Create CSV content
                output = io.StringIO()

                if votes:
                    # Get all unique logos for headers
                    all_logos = set()
                    for vote in votes:
                        all_logos.update(vote["ratings"].keys())
                    logo_columns = sorted(all_logos)

                    # Write CSV
                    fieldnames = ["id", "voter_name", "timestamp"] + logo_columns
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()

                    for vote in votes:
                        row = {
                            "id": vote["id"],
                            "voter_name": vote["voter_name"],
                            "timestamp": vote["timestamp"],
                        }
                        # Add ratings for each logo
                        for logo in logo_columns:
                            row[logo] = vote["ratings"].get(logo, "")

                        writer.writerow(row)

                return {
                    "success": True,
                    "format": "csv",
                    "data": output.getvalue(),
                    "filename": f"votes_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "count": len(votes),
                }

            elif format.lower() == "json":
                # Create JSON content
                export_data = {
                    "export_timestamp": datetime.utcnow().isoformat(),
                    "vote_count": len(votes),
                    "votes": votes,
                }

                return {
                    "success": True,
                    "format": "json",
                    "data": json.dumps(export_data, indent=2, default=str),
                    "filename": f"votes_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    "count": len(votes),
                }

            else:
                return {
                    "success": False,
                    "message": f"Unsupported export format: {format}. Use 'csv' or 'json'.",
                }

        except Exception as e:
            logger.error(f"Failed to export votes: {e}")
            return {
                "success": False,
                "message": "Export failed due to server error",
                "error": str(e),
            }

    def delete_voter_votes(self, voter_name: str) -> dict[str, Any]:
        """
        Delete all votes from a specific voter.
        Returns operation result.
        """
        try:
            with self.db_manager.get_session() as session:
                votes_to_delete = (
                    session.query(VoteRecord).filter_by(voter_name=voter_name).all()
                )
                vote_count = len(votes_to_delete)

                if vote_count == 0:
                    return {
                        "success": False,
                        "message": f"No votes found for voter '{voter_name}'",
                    }

                # Delete the votes
                session.query(VoteRecord).filter_by(voter_name=voter_name).delete()
                session.commit()

            logger.info(f"Deleted {vote_count} votes for voter: {voter_name}")
            return {
                "success": True,
                "message": f"Deleted {vote_count} votes for '{voter_name}'",
                "deleted_count": vote_count,
                "voter_name": voter_name,
            }

        except SQLAlchemyError as e:
            logger.error(f"Failed to delete votes for {voter_name}: {e}")
            return {
                "success": False,
                "message": "Failed to delete votes due to database error",
                "error": str(e),
            }

    # System Administration Methods
    def get_system_stats(self) -> dict[str, Any]:
        """Get comprehensive system statistics."""
        try:
            # Database stats
            vote_count = self.db_manager.get_vote_count()

            # Get unique voters count
            with self.db_manager.get_session() as session:
                unique_voters = session.query(VoteRecord.voter_name).distinct().count()

            # Get last vote timestamp
            votes = self.db_manager.get_all_votes()
            last_vote = None
            if votes:
                last_vote = votes[0]["timestamp"]  # Already sorted by timestamp desc

            # Logo stats
            logo_count = len(settings.get_logo_files())

            # Database file size
            db_path = Path(self.db_manager.database_path)
            db_size = "Unknown"
            if db_path.exists():
                size_bytes = db_path.stat().st_size
                if size_bytes < 1024:
                    db_size = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    db_size = f"{size_bytes / 1024:.1f} KB"
                else:
                    db_size = f"{size_bytes / (1024 * 1024):.1f} MB"

            # System uptime (approximate)
            uptime = "Unknown"
            try:
                import psutil

                boot_time = datetime.fromtimestamp(psutil.boot_time())
                uptime_delta = datetime.now() - boot_time
                days = uptime_delta.days
                hours, remainder = divmod(uptime_delta.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                uptime = f"{days}d {hours}h {minutes}m"
            except ImportError:
                # Fallback method
                uptime = "Requires psutil package"

            # Disk usage for logos directory
            disk_usage: dict[str, Any] = {}
            try:
                logos_dir_size = sum(
                    f.stat().st_size
                    for f in settings.LOGOS_DIR.glob("*")
                    if f.is_file()
                )
                disk_usage = {
                    "logos_directory_size": logos_dir_size,
                    "logos_directory_size_mb": round(logos_dir_size / (1024 * 1024), 2),
                }
            except Exception as e:
                logger.error(f"Failed to calculate disk usage: {e}")
                disk_usage = {"error": str(e)}

            # Memory usage (if psutil available)
            memory_usage: dict[str, Any] = {}
            try:
                import psutil

                memory = psutil.virtual_memory()
                memory_usage = {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_percent": memory.percent,
                }
            except ImportError:
                memory_usage = {"error": "Requires psutil package"}

            return {
                "total_votes": vote_count,
                "total_voters": unique_voters,
                "total_logos": logo_count,
                "database_size": db_size,
                "uptime": uptime,
                "last_vote": last_vote,
                "disk_usage": disk_usage,
                "memory_usage": memory_usage,
            }

        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            return {
                "error": str(e),
                "total_votes": 0,
                "total_voters": 0,
                "total_logos": 0,
                "database_size": "Unknown",
                "uptime": "Unknown",
                "last_vote": None,
                "disk_usage": {},
                "memory_usage": {},
            }

    def backup_database(self) -> dict[str, Any]:
        """Create a backup of the database."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"votes_backup_{timestamp}.db"
            backup_path = settings.BASE_DIR / "backups" / backup_filename

            # Create backups directory if it doesn't exist
            backup_path.parent.mkdir(exist_ok=True)

            # Copy database file
            db_path = Path(self.db_manager.database_path)
            if db_path.exists():
                shutil.copy2(db_path, backup_path)

                backup_size = backup_path.stat().st_size

                logger.info(f"Database backed up to: {backup_path}")
                return {
                    "success": True,
                    "message": "Database backed up successfully",
                    "backup_filename": backup_filename,
                    "backup_size": backup_size,
                    "timestamp": timestamp,
                }
            else:
                return {"success": False, "message": "Database file not found"}

        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return {
                "success": False,
                "message": "Backup failed due to server error",
                "error": str(e),
            }

    def get_recent_activity(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent voting activity."""
        try:
            votes = self.db_manager.get_all_votes()
            return votes[:limit]  # Already sorted by timestamp desc

        except Exception as e:
            logger.error(f"Failed to get recent activity: {e}")
            return []
