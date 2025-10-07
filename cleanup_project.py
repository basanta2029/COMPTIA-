#!/usr/bin/env python3
"""
Project Cleanup Script
Removes unnecessary files and folders while keeping essential RAG data
"""

import os
import shutil
from pathlib import Path
from typing import List


class ProjectCleanup:
    """Clean up unnecessary files and folders"""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.stats = {
            'folders_removed': 0,
            'files_removed': 0,
            'space_freed': 0
        }

    def get_folder_size(self, folder_path: Path) -> int:
        """Calculate total size of a folder in bytes"""
        total_size = 0
        try:
            for item in folder_path.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
        except Exception:
            pass
        return total_size

    def remove_duplicate_chapter_folders(self):
        """Remove duplicate chapter folders in root (keep only data_raw and data_clean versions)"""
        print("\n1. Removing duplicate chapter folders from root...")

        # These are duplicates - we have them in data_raw and data_clean
        duplicate_folders = [
            '01_Security_Concepts',
            '02_Threats_Vulnerabilities_and_Mitigations',
            '03_Cryptographic_Solutions',
            '04_Identity_and_Access_Management'
        ]

        for folder_name in duplicate_folders:
            folder_path = self.project_dir / folder_name
            if folder_path.exists() and folder_path.is_dir():
                size = self.get_folder_size(folder_path)
                try:
                    shutil.rmtree(folder_path)
                    self.stats['folders_removed'] += 1
                    self.stats['space_freed'] += size
                    print(f"   ✓ Removed: {folder_name} ({size // 1024} KB)")
                except Exception as e:
                    print(f"   ✗ Error removing {folder_name}: {str(e)}")

    def remove_old_txt_files_from_clean(self):
        """Remove old .txt files from data_clean (keep only .json files)"""
        print("\n2. Removing old .txt files from data_clean...")

        data_clean = self.project_dir / 'data_clean'
        if not data_clean.exists():
            print("   → data_clean folder not found, skipping")
            return

        count = 0
        size_freed = 0

        # Find all .txt files in data_clean subdirectories
        for txt_file in data_clean.rglob('*.txt'):
            if txt_file.is_file():
                try:
                    file_size = txt_file.stat().st_size
                    txt_file.unlink()
                    count += 1
                    size_freed += file_size
                    self.stats['files_removed'] += 1
                    self.stats['space_freed'] += file_size
                except Exception as e:
                    print(f"   ✗ Error removing {txt_file.name}: {str(e)}")

        if count > 0:
            print(f"   ✓ Removed {count} .txt files ({size_freed // 1024} KB)")
        else:
            print("   → No .txt files found in data_clean")

    def remove_empty_folders(self):
        """Remove empty data_summaries and data_index folders"""
        print("\n3. Removing empty utility folders...")

        empty_folders = ['data_summaries', 'data_index']

        for folder_name in empty_folders:
            folder_path = self.project_dir / folder_name
            if folder_path.exists() and folder_path.is_dir():
                # Check if empty or only has empty subdirs
                try:
                    items = list(folder_path.rglob('*'))
                    files = [item for item in items if item.is_file()]

                    if len(files) == 0:
                        shutil.rmtree(folder_path)
                        self.stats['folders_removed'] += 1
                        print(f"   ✓ Removed: {folder_name} (empty)")
                    else:
                        print(f"   → Keeping {folder_name} (has {len(files)} files)")
                except Exception as e:
                    print(f"   ✗ Error removing {folder_name}: {str(e)}")

    def remove_obsolete_scripts(self):
        """Remove obsolete scripts no longer needed"""
        print("\n4. Removing obsolete scripts...")

        obsolete_scripts = ['fix_formatting.py']

        for script_name in obsolete_scripts:
            script_path = self.project_dir / script_name
            if script_path.exists() and script_path.is_file():
                try:
                    file_size = script_path.stat().st_size
                    script_path.unlink()
                    self.stats['files_removed'] += 1
                    self.stats['space_freed'] += file_size
                    print(f"   ✓ Removed: {script_name}")
                except Exception as e:
                    print(f"   ✗ Error removing {script_name}: {str(e)}")

    def verify_essential_files(self):
        """Verify essential files are still present"""
        print("\n5. Verifying essential files...")

        essential_items = {
            'folders': [
                'data_raw',
                'data_clean',
                'data_raw/01_Security_Concepts',
                'data_raw/02_Threats_Vulnerabilities_and_Mitigations',
                'data_raw/03_Cryptographic_Solutions',
                'data_raw/04_Identity_and_Access_Management',
                'data_clean/01_Security_Concepts',
                'data_clean/02_Threats_Vulnerabilities_and_Mitigations',
                'data_clean/03_Cryptographic_Solutions',
                'data_clean/04_Identity_and_Access_Management'
            ],
            'files': [
                'data_cleaner.py',
                'summarizer.py',
                'validate_data.py',
                'README_DATA_CLEANING.md',
                'data_clean/validation_report.json'
            ]
        }

        all_present = True

        # Check folders
        for folder in essential_items['folders']:
            folder_path = self.project_dir / folder
            if not folder_path.exists():
                print(f"   ✗ Missing: {folder}")
                all_present = False

        # Check files
        for file in essential_items['files']:
            file_path = self.project_dir / file
            if not file_path.exists():
                print(f"   ✗ Missing: {file}")
                all_present = False

        if all_present:
            print("   ✓ All essential files and folders present")

        return all_present

    def print_summary(self):
        """Print cleanup summary"""
        print("\n" + "=" * 60)
        print("Cleanup Summary")
        print("=" * 60)
        print(f"Folders removed: {self.stats['folders_removed']}")
        print(f"Files removed: {self.stats['files_removed']}")
        print(f"Space freed: {self.stats['space_freed'] / 1024:.2f} KB")
        print("=" * 60)

    def run(self):
        """Execute cleanup process"""
        print("=" * 60)
        print("Project Cleanup - Removing Unnecessary Files")
        print("=" * 60)

        # Perform cleanup steps
        self.remove_duplicate_chapter_folders()
        self.remove_old_txt_files_from_clean()
        self.remove_empty_folders()
        self.remove_obsolete_scripts()

        # Verify essential files
        is_valid = self.verify_essential_files()

        # Print summary
        self.print_summary()

        if is_valid:
            print("\n✅ Cleanup complete - project is clean and ready!")
        else:
            print("\n⚠️  Cleanup complete - some essential files missing!")

        return is_valid


def main():
    """Main entry point"""
    script_dir = Path(__file__).parent
    cleaner = ProjectCleanup(script_dir)
    cleaner.run()


if __name__ == '__main__':
    main()
