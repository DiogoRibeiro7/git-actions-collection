from pathlib import Path

def test_terraform_file_has_provider():
    content = Path('examples/multi-cloud-deploy/terraform/main.tf').read_text()
    assert 'provider "aws"' in content

def test_bicep_file_exists():
    assert Path('examples/multi-cloud-deploy/azure/main.bicep').exists()
