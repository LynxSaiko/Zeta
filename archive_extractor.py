import os
import zipfile
import tarfile
import py7zr
import curses

class ArchiveExtractor:
    @staticmethod
    def extract_zip(stdscr, path, filename):
        """Handle ZIP file extraction"""
        file_path = os.path.join(path, filename)
        extract_dir = os.path.join(path, os.path.splitext(filename)[0])
        
        # Create confirmation popup
        height, width = stdscr.getmaxyx()
        popup_h = 5
        popup_w = 60
        popup = curses.newwin(popup_h, popup_w, height//2 - popup_h//2, width//2 - popup_w//2)
        popup.border()
        popup.addstr(0, 2, " Extract ZIP Archive ")
        popup.addstr(1, 2, f"File: {filename[:popup_w-10]}")
        popup.addstr(2, 2, f"To: {os.path.basename(extract_dir)[:popup_w-10]}")
        popup.addstr(3, 2, "Press Y to confirm, any key to cancel")
        popup.refresh()

        key = stdscr.getch()
        if key in [ord('y'), ord('Y')]:
            try:
                os.makedirs(extract_dir, exist_ok=True)
                with zipfile.ZipFile(file_path, 'r') as archive:
                    archive.extractall(extract_dir)
                return True, f"Extracted to {os.path.basename(extract_dir)}"
            except Exception as e:
                return False, f"Extraction failed: {str(e)}"
        return False, "Cancelled"

    @staticmethod
    def extract_tar_gz(stdscr, path, filename):
        """Handle TAR.GZ file extraction"""
        return ArchiveExtractor._extract_tar(stdscr, path, filename, 'gz')

    @staticmethod
    def extract_tar_xz(stdscr, path, filename):
        """Handle TAR.XZ file extraction"""
        return ArchiveExtractor._extract_tar(stdscr, path, filename, 'xz')

    @staticmethod
    def extract_pkg_tar_xz(stdscr, path, filename):
        """Handle PKG.TAR.XZ file extraction"""
        return ArchiveExtractor._extract_tar(stdscr, path, filename, 'xz')

    @staticmethod
    def extract_tar(stdscr, path, filename):
        """Handle TAR file extraction (without compression)"""
        return ArchiveExtractor._extract_tar(stdscr, path, filename, 'none')

    @staticmethod
    def _extract_tar(stdscr, path, filename, mode):
        """Internal method for tar extraction"""
        file_path = os.path.join(path, filename)
        extract_dir = os.path.join(path, os.path.splitext(filename)[0].replace('.tar',''))
        
        if mode == 'none':
            ext_type = 'TAR'
        else:
            ext_type = 'GZ' if mode == 'gz' else 'XZ'

        height, width = stdscr.getmaxyx()
        popup_h = 5
        popup_w = 60
        popup = curses.newwin(popup_h, popup_w, height//2 - popup_h//2, width//2 - popup_w//2)
        popup.border()
        popup.addstr(0, 2, f" Extract {ext_type} Archive ")
        popup.addstr(1, 2, f"File: {filename[:popup_w-10]}")
        popup.addstr(2, 2, f"To: {os.path.basename(extract_dir)[:popup_w-10]}")
        popup.addstr(3, 2, "Press Y to confirm, any key to cancel")
        popup.refresh()

        key = stdscr.getch()
        if key in [ord('y'), ord('Y')]:
            try:
                os.makedirs(extract_dir, exist_ok=True)
                if mode == 'none':
                    with tarfile.open(file_path, 'r') as archive:
                        archive.extractall(extract_dir)
                else:
                    with tarfile.open(file_path, f'r:{mode}') as archive:
                        archive.extractall(extract_dir)
                return True, f"Extracted to {os.path.basename(extract_dir)}"
            except Exception as e:
                return False, f"Extraction failed: {str(e)}"
        return False, "Cancelled"
    
    # New Methods for Compression

    @staticmethod
    def compress_to_zip(stdscr, path, folder_name, output_zip):
        """Handle Compression to ZIP"""
        folder_path = os.path.join(path, folder_name)
        try:
            with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
                for foldername, subfolders, filenames in os.walk(folder_path):
                    for filename in filenames:
                        file_path = os.path.join(foldername, filename)
                        arcname = os.path.relpath(file_path, folder_path)
                        zip_ref.write(file_path, arcname)
            return True, f"Compressed '{folder_name}' to '{output_zip}'"
        except Exception as e:
            return False, f"Compression failed: {str(e)}"

    @staticmethod
    def compress_to_tar_gz(stdscr, path, folder_name, output_tar):
        """Handle Compression to TAR.GZ"""
        folder_path = os.path.join(path, folder_name)
        try:
            with tarfile.open(output_tar, 'w:gz') as tar_ref:
                tar_ref.add(folder_path, arcname=os.path.basename(folder_path))
            return True, f"Compressed '{folder_name}' to '{output_tar}'"
        except Exception as e:
            return False, f"Compression failed: {str(e)}"

    @staticmethod
    def compress_to_7z(stdscr, path, folder_name, output_7z):
        """Handle Compression to 7z"""
        folder_path = os.path.join(path, folder_name)
        try:
            with py7zr.SevenZipFile(output_7z, mode='w') as z:
                z.writeall(folder_path, os.path.basename(folder_path))
            return True, f"Compressed '{folder_name}' to '{output_7z}'"
        except Exception as e:
            return False, f"Compression failed: {str(e)}"

    # New Method for Listing Available Formats
    @staticmethod
    def get_supported_formats():
        return ['.zip', '.tar.gz', '.tar.xz', '.pkg.tar.xz', '.tar', '.7z']
