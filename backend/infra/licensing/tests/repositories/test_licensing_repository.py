from infra.licensing.repositories.licensing_repository import LicensingRepository


def test_licensing_repository_class_is_importable():
    # The licensing module is a placeholder. This smoke test ensures the
    # class is importable; replace with real tests once persistence is added.
    assert LicensingRepository is not None
    assert LicensingRepository() is not None
