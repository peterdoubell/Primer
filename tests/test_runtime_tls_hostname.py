"""The IDNA2003 alias must not authenticate an IDNA2008 TLS hostname."""
import datetime
import socket
import ssl
import threading

import anyio
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

@pytest.mark.parametrize('certificate_hostname,accepted', [('fass.invalid',False),('xn--fa-hia.invalid',True)])
def test_unicode_hostname_is_verified_against_its_IDNA2008_certificate(tmp_path,certificate_hostname,accepted):
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    subject=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,certificate_hostname)])
    now=datetime.datetime.now(datetime.timezone.utc)
    cert=(x509.CertificateBuilder().subject_name(subject).issuer_name(subject).public_key(key.public_key())
          .serial_number(x509.random_serial_number()).not_valid_before(now-datetime.timedelta(minutes=1))
          .not_valid_after(now+datetime.timedelta(days=1))
          .add_extension(x509.SubjectAlternativeName([x509.DNSName(certificate_hostname)]),critical=False)
          .add_extension(x509.BasicConstraints(ca=True,path_length=None),critical=True).sign(key,hashes.SHA256()))
    cert_path=tmp_path/'local-test-cert.pem';key_path=tmp_path/'local-test-key.pem'
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
    server_context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);server_context.load_cert_chain(cert_path,key_path)
    client_context=ssl.create_default_context(cafile=str(cert_path))
    errors=[]
    with socket.socket() as listener:
        listener.bind(('127.0.0.1',0));listener.listen(1);listener.settimeout(10);port=listener.getsockname()[1]
        def server():
            try:
                connection,_=listener.accept();connection.settimeout(10)
                with server_context.wrap_socket(connection,server_side=True) as encrypted:
                    encrypted.sendall(b'verified')
                    encrypted.recv(1)
                    encrypted.unwrap().close()
            except ssl.SSLError as error:
                errors.append(error)
        thread=threading.Thread(target=server,daemon=True);thread.start()
        async def connect():
            with anyio.fail_after(10):
                async with await anyio.connect_tcp('127.0.0.1',port,tls=True,tls_hostname='faß.invalid',ssl_context=client_context) as stream:
                    return await stream.receive()
        try:
            if accepted:
                assert anyio.run(connect)==b'verified'
            else:
                with pytest.raises(ssl.SSLCertVerificationError):anyio.run(connect)
        finally:
            thread.join(10)
            assert not thread.is_alive(), 'Loopback TLS verification server did not terminate'
        if accepted:assert not errors
