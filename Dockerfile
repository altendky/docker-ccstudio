FROM ubuntu:18.04

WORKDIR /ccs_install

RUN apt-get update
RUN apt-get install -y wget bash
RUN wget --no-verbose http://software-dl.ti.com/ccs/esd/CCSv8/CCS_8_0_0/exports/CCS8.0.0.00016_linux-x64.tar.gz
RUN tar -xvf CCS8.0.0.00016_linux-x64.tar.gz

RUN dpkg --add-architecture i386 && apt-get update && apt-get install -y \
  libc6:i386                    \
  libx11-6:i386                 \
  libasound2:i386               \
  libatk1.0-0:i386              \
  libcairo2:i386                \
  libcups2:i386                 \
  libdbus-glib-1-2:i386         \
  libgconf-2-4:i386             \
  libgcrypt20:i386              \
  libgdk-pixbuf2.0-0:i386       \
  libgtk-3-0:i386               \
  libice6:i386                  \
  libncurses5:i386              \
  libsm6:i386                   \
  liborbit2:i386                \
  libudev1:i386                 \
  libusb-0.1-4:i386             \
  libstdc++6:i386               \
  libstdc++6					\
  libxt6						\
  libxt6:i386                   \
  libxtst6:i386                 \
  libgnomeui-0:i386             \
  libusb-1.0-0-dev:i386         \
  libcanberra-gtk-module:i386   \
  gtk2-engines-murrine:i386     \
  libpython2.7				    \
  unzip         				\
  wget

# ADD CCS8.0.0.00016_linux-x64.tar.gz /ccs_install
COPY ccstudio_installation_responses /ccs_install

# https://e2e.ti.com/support/development_tools/code_composer_studio/f/81/t/374161
RUN /ccs_install/CCS8.0.0.00016_linux-x64/ccs_setup_linux64_8.0.0.00016.bin --mode unattended --prefix /opt/ti --response-file /ccs_install/ccstudio_installation_responses

RUN /opt/ti/ccsv8/eclipse/ccstudio -application org.eclipse.equinox.p2.director -noSplash -repository http://software-dl.ti.com/dsps/dsps_public_sw/sdo_ccstudio/codegen/Updates/p2linux -installIUs com.ti.cgt.c2000.6.4.linux.feature.group

RUN rm -r /ccs_install

ENV PATH="/opt/ti/ccsv8/eclipse:${PATH}"

# workspace folder for CCS
RUN mkdir /workspace

# directory for the ccs project
VOLUME /wd
WORKDIR /wd
