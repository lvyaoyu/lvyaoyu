# coding: utf-8
import re
import sys
import os


class WechatImageDecoder:
    def __init__(self, dat_file, target_dir=None):
        self.dat_file = dat_file.lower()
        self.target_dir = target_dir
        self.file_path = None

    def run(self):
        if self.target_dir and not os.path.isdir(self.target_dir):
            print(self.target_dir, '不是一个目录')
            return
        decoder = self._match_decoder()
        decoder()

        return self.file_path

    def _match_decoder(self):
        decoders = {
            r'.+\.dat$': self._decode_pc_dat,
            r'cache\.data\.\d+$': self._decode_android_dat,
            None: self._decode_unknown_dat,
        }

        for k, v in decoders.items():
            if k is not None and re.match(k, self.dat_file):
                return v
        return decoders[None]

    def _decode_pc_dat(self):

        def do_magic(header_code, buf):
            return header_code ^ list(buf)[0] if buf else 0x00

        def decode(magic, buf):
            return bytearray([b ^ magic for b in list(buf)])

        def guess_encoding(buf):
            headers = {
                'jpg': (0xff, 0xd8),
                'png': (0x89, 0x50),
                'gif': (0x47, 0x49),
            }
            for encoding in headers:
                header_code, check_code = headers[encoding]
                magic = do_magic(header_code, buf)
                _, code = decode(magic, buf[:2])
                if check_code == code:
                    return (encoding, magic)
            print('Decode failed')
            sys.exit(1)

        with open(self.dat_file, 'rb') as f:
            buf = bytearray(f.read())
        file_type, magic = guess_encoding(buf)

        img_file = re.sub(r'.dat$', '.' + file_type, self.dat_file)

        if self.target_dir:
            img_file = os.path.join(self.target_dir, os.path.split(img_file)[-1])

        with open(img_file, 'wb') as f:
            new_buf = decode(magic, buf)
            f.write(new_buf)

        print('解密完成', img_file)
        self.file_path = img_file

    def _decode_android_dat(self):
        with open(self.dat_file, 'rb') as f:
            buf = f.read()

        last_index = 0
        imgfile = ''
        for i, m in enumerate(re.finditer(b'\xff\xd8\xff\xe0\x00\x10\x4a\x46', buf)):
            if m.start() == 0:
                continue

            imgfile = '%s_%d.jpg' % (self.dat_file, i)
            if self.target_dir:
                imgfile = os.path.join(self.target_dir, os.path.split(imgfile)[-1])
            with open(imgfile, 'wb') as f:
                f.write(buf[last_index: m.start()])
            last_index = m.start()
        print('解密完成', imgfile)
        self.file_path = imgfile

    def _decode_unknown_dat(self):
        raise Exception('Unknown file type')


if __name__ == '__main__':
    # wd = WechatImageDecoder(
    #     r'C:\Users\EDZ\Documents\WeChat Files\wxid_hb1rphct88wi22\FileStorage\Image\2020-12\ff6848f8fba8b4b7edb0e2d19e16ba1a.dat',
    #     r'C:\Users\EDZ\PycharmProjects\test\hpsocket_exanple\images')
    wd = WechatImageDecoder(
        r'C:\Users\EDZ\Documents\WeChat Files\wxid_hb1rphct88wi22\FileStorage\Image\2020-12\ff6848f8fba8b4b7edb0e2d19e16ba1a.dat')
    print(wd.run())
