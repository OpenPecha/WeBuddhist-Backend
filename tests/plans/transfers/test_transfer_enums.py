from pecha_api.plans.transfers.transfer_enums import ContentTransferStatus, normalize_transfer_status


def test_normalize_transfer_status_from_enum():
    assert normalize_transfer_status(ContentTransferStatus.PENDING) == ContentTransferStatus.PENDING


def test_normalize_transfer_status_from_string():
    assert normalize_transfer_status("PENDING") == ContentTransferStatus.PENDING
