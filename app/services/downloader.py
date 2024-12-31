import subprocess
import logging
import os
from datetime import datetime
import shutil
from typing import Dict

from ..config import settings

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DownloadService:
    def __init__(self):
        self.downloads: Dict[str, Dict] = {}
        os.makedirs(settings.DOWNLOAD_DIR, exist_ok=True)

    async def execute_download(self, url: str, download_id: str) -> Dict:
        try:
            logger.info(f"Starting download {download_id} for URL: {url}")
            
            # 作業ディレクトリの設定
            temp_dir = os.path.join(settings.DOWNLOAD_DIR, f"temp_{download_id}")
            os.makedirs(temp_dir, exist_ok=True)
            
            # 出力ファイル名の設定
            final_output = os.path.join(settings.DOWNLOAD_DIR, f"space_{download_id}.m4a")
            temp_output = os.path.join(temp_dir, "download.m4a")
            
            # cookies.txtの存在確認
            if not os.path.exists(settings.cookies_path):
                logger.error(f"Cookies file not found at {settings.cookies_path}")
                return {
                    "status": "failed",
                    "download_id": download_id,
                    "error": "Cookies file not found",
                    "completed_at": datetime.now().isoformat()
                }
            
            # コマンドの構築（元のシンプルな形式）
            #command = f"twspace_dl -i {url} -c {settings.cookies_path} -o {temp_output} -v"
            command = f"twspace_dl -i {url} -c {settings.cookies_path}"
            
            logger.info(f"Executing command: {command}")
            
            # プロセスの実行
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=temp_dir
            )

            # 出力の処理
            stdout_data, stderr_data = process.communicate()
            
            if stdout_data:
                logger.info(f"STDOUT: {stdout_data}")
            if stderr_data:
                logger.error(f"STDERR: {stderr_data}")

            # 結果の処理
            if process.returncode == 0 and os.path.exists(temp_output):
                # 成功時の処理
                shutil.move(temp_output, final_output)
                logger.info(f"Download completed: {final_output}")
                
                result = {
                    "status": "completed",
                    "download_id": download_id,
                    "file_path": final_output,
                    "space_url": url,
                    "completed_at": datetime.now().isoformat()
                }
            else:
                # エラー時の処理
                error_msg = f"Download failed with return code {process.returncode}"
                if stderr_data:
                    error_msg += f": {stderr_data}"
                logger.error(f"{error_msg} for {download_id}")
                
                result = {
                    "status": "failed",
                    "download_id": download_id,
                    "error": error_msg,
                    "stderr": stderr_data,
                    "completed_at": datetime.now().isoformat()
                }

            # クリーンアップ
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Failed to clean up temp directory: {e}")
            
            return result

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"{error_msg} for {download_id}", exc_info=True)
            return {
                "status": "failed",
                "download_id": download_id,
                "error": error_msg,
                "completed_at": datetime.now().isoformat()
            }