{ pkgs }: {
    deps = [
        pkgs.ffmpeg
        pkgs.libopus
        pkgs.libvpx
        pkgs.yasm
        pkgs.pkg-config
    ];
}
