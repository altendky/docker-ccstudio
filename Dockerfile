ARG FROM="ubuntu:focal-20210217"
FROM $FROM

ARG TARBALL=cache/ccs.tar.gz
ARG COMPILER_VERSION=6.4

ARG IU=

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8


WORKDIR /ccs_install

COPY "$TARBALL" .

RUN apt-get update

ADD install-packages.sh .
RUN ./install-packages.sh \
  --option APT::Immediate-Configure=false \
  libc6:i386 \
  libx11-6:i386 \
  libasound2:i386 \
  libatk1.0-0:i386 \
  libcairo2:i386 \
  libcups2:i386 \
  libdbus-glib-1-2:i386 \
  libgconf-2-4:i386 \
  libgcrypt20:i386 \
  libgdk-pixbuf2.0-0:i386 \
  libgtk-3-0:i386 \
  libice6:i386 \
  libncurses5:i386 \
  libncurses5:amd64 \
  libsm6:i386 \
  libudev1:i386 \
  libusb-0.1-4:i386 \
  libusb-0.1-4:amd64 \
  libstdc++6:i386 \
  libstdc++6 \
  libxt6 \
  libxt6:i386 \
  libxtst6:i386 \
  libusb-1.0-0-dev:i386 \
  libcanberra-gtk-module:i386 \
  libcanberra-gtk-module:amd64 \
  gtk2-engines-murrine:i386 \
  libpython2.7 \
  openjdk-8-jdk \
  openjdk-8-jre \
  openjdk-8-jdk-headless \
  openjdk-8-jre-headless \
  unzip \
  libc6:amd64 \
  libexpat1:amd64 \
  zlib1g:amd64 \
  libgcc1:amd64 \
  base-files \
  \
  python3 \
  \
  gcc \
  libdpkg-perl \
  lsb-release git \
  autoconf \
  libtool \
  curl \
  vim \
  nano \
  tree \
  xvfb \
  x11vnc

COPY docker.py .
RUN python3 -m venv install_env \
  && install_env/bin/pip install --upgrade pip setuptools wheel \
  && install_env/bin/pip install psutil \
  && install_env/bin/python3 docker.py \
  && rm -rf install_env docker.py

# workspace folder for CCS
RUN mkdir /workspace

# directory for the ccs project
VOLUME /wd
WORKDIR /wd

COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
