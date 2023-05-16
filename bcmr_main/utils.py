from subprocess import Popen, PIPE


# OP_RETURN 'BCMR' <bcmr_json_hash> <encoded_bcmr_url>
def decode_bcmr_op_url(encoded_bcmr_url):
    cmd = f'node bcmr_main/js/decode_bcmr_op_url.js {encoded_bcmr_url}'
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    result = stdout.decode('utf8')
    return result
