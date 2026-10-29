import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from project import read_project, save_project


class ProjectTests(unittest.TestCase):
    def test_roundtrip_and_missing_source(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)
            source=folder/'sample.HED';source.write_bytes(b'example')
            project=folder/'study.qvp'
            interval=(datetime(2026,10,8,12),datetime(2026,10,8,13))
            save_project(project,source,{'titulo_proyecto':'Energía'},['V1_Avg [V]'],interval,'Notas del sitio')
            restored=read_project(project)
            self.assertEqual(restored['source'],source.resolve())
            self.assertEqual(restored['config']['titulo_proyecto'],'Energía')
            self.assertEqual(tuple(restored['interval']),interval)
            self.assertEqual(restored['notes'],'Notas del sitio')
            source.unlink()
            with self.assertRaises(ValueError):read_project(project)


if __name__=='__main__':unittest.main()
