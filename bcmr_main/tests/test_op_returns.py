import pytest
from bcmr_main.op_return import process_op_return
from bcmr_main.utils import timestamp_to_date
from bcmr_main.models import Registry

pytestmark = pytest.mark.django_db


VALID_OP_RETURNS = [
    # BitCats BCMR
    (
        '3ed294f4894f159125a87a6e6681f0dd71d3b2f51c275a15b502138aba3399c8',
        '07275f68d14780c737279898e730cec3a7b189a761caf43b4197b60a7c891a97',
        'OP_RETURN 1380795202 65353166303362396131373738636536373032616365323437393230313231646361303730653365356166643066333062356530383961306363376330303635 697066732e7061742e6d6e2f697066732f516d5155765a675763737231535755426f7a78537066704257646f4a376259764474566e35556233705447784455',
        1685966924,
        'https://ipfs.pat.mn/ipfs/QmQUvZgWcsr1SWUBozxSpfpBWdoJ7bYvDtVn5Ub3pTGxDU'
    ),
    # Fallout token BCMR
    (
        '2edbe1d87de2a93f26cf4764342f67b0fdba51f05ae3cc067c1ac3746454afcb',
        '83e12eea20b19a9a0906bb0521ff18520db69a4a8136293bafbfca0acb2c2313',
        'OP_RETURN 1380795202 a8dd9f3f77efec7d4c159cbd28f6181e704dd0c298baea0cc3488cd1a176dc91 63332d736f66742e636f6d2f746f6b656e732f66616c6c6f75745f636f696e2e6a736f6e',
        1684157526,
        'https://c3-soft.com/tokens/fallout_coin.json'
    )
]


@pytest.mark.django_db
class TestOpReturnValidation:

    @pytest.mark.parametrize("txid, category, op_return, date, bcmr_url", VALID_OP_RETURNS)
    def test_op_return_validation(self, txid, category, op_return, date, bcmr_url):
        date = timestamp_to_date(date)
        encoded_bcmr_json_hash = op_return.split(' ')[2]
        encoded_bcmr_url = op_return.split(' ')[3]

        # Check if registry table is empty
        registries = Registry.objects.all()
        assert registries.count() == 0

        # Check if the BCMR is found valid
        is_valid, decoded_bcmr_url = process_op_return(
            txid,
            encoded_bcmr_json_hash,
            encoded_bcmr_url,
            op_return,
            category,
            date
        )
        assert is_valid, decoded_bcmr_url == bcmr_url

        # Check if the record for this BCMR is saved in the registry table
        registries = Registry.objects.all()
        assert registries.count() == 1

        registry = registries.first()
        assert registry.txid == txid
        assert registry.category == category
        assert registry.op_return == op_return
        assert registry.bcmr_url == bcmr_url
