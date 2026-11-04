FROM odoo:19

USER root

#COPY ./requirements_new.txt /mnt/extra-addons/

#RUN pip3 install --no-cache-dir -r /mnt/extra-addons/requirements_new.txt

COPY extra-addons/ /mnt/extra-addons/
COPY ./odoo.conf /etc/odoo/odoo.conf
#COPY integration-addons/ /mnt/integration-addons/
#COPY external-addons/ /mnt/external-addons/
#COPY addons/ /mnt/addons

USER odoo
