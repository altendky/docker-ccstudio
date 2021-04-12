ARG FROM="ubuntu:focal-20210217"

FROM $FROM as common

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8


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
  gcc \
  g++ \
  make \
  libdpkg-perl \
  lsb-release \
  git \
  autoconf \
  autotools-dev \
  automake \
  libtool \
  curl \
  vim \
  nano \
  tree \
  clang \
  \
  bear \
  clang-tidy \
  pylint3 \
  flake8 \
  mypy \
  \
  xvfb \
  x11vnc \
  \
  ca-certificates

FROM common as build

ARG TARBALL=cache/ccs.tar.gz
ARG INSTALL_IU=
ARG UNINSTALL_IU=

WORKDIR /ccs_install

COPY "$TARBALL" the.tar.gz

COPY docker.py .

ADD install-packages.sh .
RUN ./install-packages.sh \
  python3 \
  python3-venv

RUN apt-get install -y tar
RUN apt-get install -y curl

RUN curl --location https://github.com/oclint/oclint/releases/download/v21.03/oclint-21.03-llvm-11.1.0-x86_64-linux-ubuntu-20.04.tar.gz | tar -xz
RUN pwd
RUN ls
RUN python3 -m venv install_env
RUN install_env/bin/pip install --upgrade pip setuptools wheel
RUN install_env/bin/pip install click psutil
RUN install_env/bin/python3 docker.py --tarball the.tar.gz --install-iu "$INSTALL_IU" --uninstall-iu "$UNINSTALL_IU"

FROM common
COPY --from=build /opt/ti/ccs /opt/ti/ccs
COPY --from=build oclint-21.03/ /oclint-21.03/
RUN pwd
RUN ls -la

RUN ln -s /opt/ti/ccs/eclipse/ccstudio /usr/bin/

# workspace folder for CCS
RUN mkdir /workspace

# directory for the ccs project
VOLUME /wd
WORKDIR /wd

COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
