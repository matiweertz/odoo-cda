FROM python:3.12-slim-bookworm

ARG ODOO_VERSION=19.0
ARG AUTOINSTALL=YES
ENV AUTOINSTALL=$AUTOINSTALL

# Variables de entorno
ENV LANG=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONPATH=/home/bo/odoo \
    ODOO_RC=/etc/odoo/odoo.conf

SHELL ["/bin/bash", "-xo", "pipefail", "-c"]

# 1. Instalar dependencias del sistema y herramientas de compilación
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    curl -fsSL https://raw.githubusercontent.com/odoo/odoo/${ODOO_VERSION}/debian/control -o /tmp/control && \
    sed -n '/^Depends:/,/^[A-Z]/p' /tmp/control \
      | awk '/^ [a-z]/ { gsub(/,/,"") ; gsub(" ", "") ; print $NF }' | sort -u \
      | xargs apt-get install -y --no-install-recommends && \
    apt-get install -y --no-install-recommends \
      build-essential \
      ca-certificates \
      git \
      npm \
      node-less \
      xz-utils \
      swig \
      python3-dev \
      libldap2-dev \
      libcairo2-dev \
      libsasl2-dev \
      libcups2-dev \
      libpq-dev && \
    curl -fsSL https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/wkhtmltox_0.12.6.1-3.bookworm_amd64.deb -o wkhtmltox.deb && \
    echo 'e9f95436298c77cc9406bd4bbd242f4771d0a4b2 wkhtmltox.deb' | sha1sum -c - && \
    apt-get install -y --no-install-recommends ./wkhtmltox.deb && \
    rm wkhtmltox.deb && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/control

# 2. Instalar rtlcss
RUN npm install -g rtlcss && npm cache clean --force

# 3. Ajuste SSL para compatibilidad con AFIP
RUN sed -i 's/^\(CipherString\s*=\s*\).*/\1DEFAULT@SECLEVEL=1/' /etc/ssl/openssl.cnf || \
    echo "CipherString = DEFAULT@SECLEVEL=1" >> /etc/ssl/openssl.cnf

# 4. Crear usuario y directorios
RUN groupadd -r odoo && \
    useradd -r -g odoo -u 1000 -d /home/bo -s /bin/bash odoo && \
    mkdir -p /home/bo /var/lib/odoo /etc/odoo /opt/venv && \
    chown -R odoo:odoo /home/bo /var/lib/odoo /etc/odoo /opt/venv && \
    su - odoo -c "python3 -m venv /opt/venv"

ENV PATH="/opt/venv/bin:$PATH"

# 5. Instalar dependencias de Python en el entorno virtual
RUN pip install --no-cache-dir --upgrade pip setuptools && \
    curl -fsSL https://raw.githubusercontent.com/odoo/odoo/${ODOO_VERSION}/requirements.txt -o /tmp/requirements.txt && \
    pip install --no-cache-dir \
      -r /tmp/requirements.txt \
      phonenumbers \
      rlPyCairo \
      google-auth \
      pygments \
      pdfminer.six && \
    rm /tmp/requirements.txt && \
    chown -R odoo:odoo /opt/venv

# 6. Clonar el repositorio fuente de Odoo 19.0 (Se cachea si no cambia la versión)
RUN git clone --depth 1 --branch ${ODOO_VERSION} https://github.com/odoo/odoo.git /home/bo/odoo && \
    chown -R odoo:odoo /home/bo/odoo

# 7. Copiar archivos de configuración y Entrypoint
COPY ./entrypoint.sh /entrypoint.sh
COPY ./odoo.conf /etc/odoo/odoo.conf
RUN chmod +x /entrypoint.sh && chown -R odoo:odoo /entrypoint.sh /etc/odoo

VOLUME ["/var/lib/odoo"]
EXPOSE 8069 8071 8072

USER odoo

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python3", "/home/bo/odoo/odoo-bin"]
