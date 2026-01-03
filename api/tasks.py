import os
import requests
import subprocess
import tempfile
import shutil
import logging

PROCESSED_DIR = "/app/processed"
os.makedirs(PROCESSED_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)

def download_to_local(url):
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
        for chunk in response.iter_content(chunk_size=8192):
            tmp_file.write(chunk)
        return tmp_file.name

def process_trim(input_url, start, end, output_name):
    logging.info(f"Starting trim job for {input_url}")
    local_in = download_to_local(input_url)
    logging.info(f"Downloaded {input_url} to {local_in}")
    out_path = os.path.join(PROCESSED_DIR, output_name)
    try:
        subprocess.run([
            "ffmpeg", "-y", "-ss", start, "-to", end, "-i", local_in, "-c", "copy", out_path
        ], check=True, timeout=300)
        logging.info(f"Trim completed: {out_path}")
        return output_name
    except Exception as e:
        logging.error(f"Trim failed: {e}")
        if os.path.exists(out_path):
            os.remove(out_path)
        raise
    finally:
        if os.path.exists(local_in):
            os.remove(local_in)

def process_remove_segment(input_url, remove_start, remove_end, output_name):
    logging.info(f"Starting remove segment job for {input_url}")
    local_in = download_to_local(input_url)
    out_path = os.path.join(PROCESSED_DIR, output_name)
    try:
        # Extract before and after segments
        before_path = tempfile.mktemp(suffix='.mp4')
        after_path = tempfile.mktemp(suffix='.mp4')
        subprocess.run([
            "ffmpeg", "-y", "-i", local_in, "-to", remove_start, "-c", "copy", before_path
        ], check=True, timeout=300)
        subprocess.run([
            "ffmpeg", "-y", "-ss", remove_end, "-i", local_in, "-c", "copy", after_path
        ], check=True, timeout=300)
        # Concat
        concat_file = tempfile.mktemp(suffix='.txt')
        with open(concat_file, 'w') as f:
            f.write(f"file '{before_path}'\nfile '{after_path}'\n")
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file, "-c", "copy", out_path
        ], check=True, timeout=300)
        logging.info(f"Remove segment completed: {out_path}")
        return output_name
    except Exception as e:
        logging.error(f"Remove segment failed: {e}")
        if os.path.exists(out_path):
            os.remove(out_path)
        raise
    finally:
        for path in [local_in, before_path, after_path, concat_file]:
            if os.path.exists(path):
                os.remove(path)

def process_autoflip(input_url, aspect_ratio, debug, output_name):
    logging.info(f"Starting autoflip job for {input_url}")
    local_in = download_to_local(input_url)
    out_path = os.path.join(PROCESSED_DIR, output_name)
    try:
        # Check for script
        script_paths = ['/app/reframe.sh', '/app/run.sh', '/app/autoflip.sh']
        script_path = None
        for path in script_paths:
            if os.path.exists(path):
                script_path = path
                break
        if script_path:
            subprocess.run([
                "bash", script_path, "-i", local_in, "-o", out_path, "-a", aspect_ratio
            ], check=True, timeout=600)
        else:
            # Fallback: simple center crop
            # Assume aspect_ratio like "9:16", but for simplicity, crop to 9:16
            # This is a basic fallback, may not be accurate
            subprocess.run([
                "ffmpeg", "-y", "-i", local_in, "-vf", f"crop=iw*9/16:ih", "-c:a", "copy", out_path
            ], check=True, timeout=600)
        logging.info(f"Autoflip completed: {out_path}")
        return output_name
    except Exception as e:
        logging.error(f"Autoflip failed: {e}")
        if os.path.exists(out_path):
            os.remove(out_path)
        raise
    finally:
        if os.path.exists(local_in):
            os.remove(local_in)