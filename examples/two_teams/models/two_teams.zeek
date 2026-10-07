# The Zeek configuration the generated traffic is read with. In a real scenario this is the
# target network's own script, captured at collect time and reused unchanged, so that real
# and generated traffic are read by the same instrument. This one loads the base analysers
# for the protocols the examples speak; a fingerprint capability such as TLS_JA4 needs the
# package that produces it loaded here and present in the sensor's image.
@load base/protocols/conn
@load base/protocols/http
@load base/protocols/ssl
@load base/files/x509
@load base/protocols/dns
@load base/protocols/ssh
@load base/protocols/smb
@load base/protocols/krb
@load base/protocols/ntlm
@load base/protocols/dce-rpc
