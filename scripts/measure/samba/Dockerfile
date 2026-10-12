# An SMB server for the measurement: one user, one share with one file. Not the samba
# runtime (impls), which comes later; just something a Windows client can log on to.
FROM debian:trixie-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends samba \
    && rm -rf /var/lib/apt/lists/*
RUN useradd --no-create-home tiergen \
    && printf 'Tiergen-2026!\nTiergen-2026!\n' | smbpasswd -a -s tiergen \
    && mkdir -p /srv/share \
    && echo hello > /srv/share/hello.txt \
    && chown -R tiergen /srv/share
COPY smb.conf /etc/samba/smb.conf
CMD ["smbd", "--foreground", "--no-process-group", "--debug-stdout"]
