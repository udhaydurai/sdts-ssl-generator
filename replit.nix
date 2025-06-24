{ pkgs }: {
  deps = [
    pkgs.python39
    pkgs.python39Packages.pip
    pkgs.python39Packages.virtualenv
    pkgs.gcc
    pkgs.libffi
    pkgs.openssl
  ];
} 