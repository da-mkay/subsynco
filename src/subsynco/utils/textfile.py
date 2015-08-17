#!/usr/bin/env python
'''
SubSynco - a tool for synchronizing subtitle files
Copyright (C) 2015  da-mkay

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import sys
if sys.platform == 'win32':
    # python-magic would require Cygwin on windows, so we fall back to
    # chardet.
    import chardet
else:
    import magic
import codecs
import re

class TextFile(object):
    @staticmethod
    def detect_encoding(file_):
        blob = open(file_).read()
        # utf8 files with BOM are not correctly detected by
        # magic/chardet --> check manually for BOM
        if blob.startswith(codecs.BOM_UTF8):
            return 'utf-8-sig'
        # Detect charset using chardet on windows and magic on other
        # platforms.
        if sys.platform == 'win32':
            encoding = chardet.detect(blob)['encoding']
            if encoding is None:
                return None
            encoding = encoding.replace('-', '_').lower()
            encoding = TextFile._fix_chardet_iso_8859_7(blob, encoding)
        else:
            m = magic.open(magic.MAGIC_MIME_ENCODING)
            m.load()
            encoding = m.buffer(blob).replace('-', '_').lower()
        # Try to fix wrong detected encodings
        encoding = TextFile._fix_latin1_latin2(blob, encoding)
        if encoding in TextFile.get_available_encodings():
            return encoding
        return None

    @staticmethod
    def _fix_chardet_iso_8859_7(blob, detected_encoding):
        """Check if the iso-8859-7 (greek) detected by chardet should be
        latin1.
        
        chardet does not support latin1 which is often used for german
        texts. chardet often detects iso-8859-7 instead. Here we check
        if iso-8859-7 was detected and if so we search for typical
        german character-sequences. If enough is found we assume the
        encoding should be latin1.
        
        Returns 'latin1' or the passed detected_encoding.
        """
        if detected_encoding in ['iso8859_7', 'iso-8859-7', 'greek', 'greek8',
                                 'iso_8859_7']:
            # Frequent german character-sequences:
            part_exists = {
                'der': 0,
                'sch': 0,
                'er': 0,
                'en': 0,
            }
            pat_german = re.compile(r'(der|sch|er\b|en\b)', re.IGNORECASE)
            for s in pat_german.findall(blob):
                if len(s) == 1:
                    part_exists[s] = 1
                else:
                    part_exists[s.lower()] = 1
            score = sum(part_exists.values())
            if score > 1:
                detected_encoding = 'latin1'
        return detected_encoding

    @staticmethod
    def _fix_latin1_latin2(blob, detected_encoding):
        """Check if the detected latin1/latin2 should be cp1252.
        
        If latin1 or latin2 was detected we check for bytes in the range
        from 0x7F to 0x9F. These are undefined for latin1/latin2 but
        they exist in cp1252 which is a superset of latin1. If any of
        these characters is found, we assume the encoding should be
        cp1252.
        
        Returns 'cp1252' or the passed detected_encoding.
        """
        if detected_encoding in ['latin_1', 'iso_8859_1', 'iso-8859-1',
                                 'iso8859-1', '8859', 'cp819', 'latin',
                                 'latin1', 'L1', 'iso_8859_2', 'iso8859_2',
                                 'iso-8859-2', 'latin2', 'L2']:
            unsupported_chars = map(chr, [128, 130, 131, 132, 133, 134, 135,
                                          136, 137, 138, 139, 140, 142, 145,
                                          146, 147, 148, 149, 150, 151, 152,
                                          153, 154, 155, 156, 158, 159])
            for char in unsupported_chars:
                if blob.find(char) >= 0:
                    detected_encoding = 'cp1252'
                    break
        return detected_encoding

    @staticmethod
    def get_available_encodings():
        return ['utf8', 'maccyrillic', 'chinese', 'mskanji', 's_jis', 'cp1140',
            'euc_jp', 'cp932', 'cp424', 'iso_2022_jp_2004', 'ibm1140',
            'eucjis2004', 'iso_2022_jp', 'iso_8859_16', 'utf_7', 'macgreek',
            'cp500', 'eucjp', 'iso_2022_jp_1', '932', 'ibm1026', 'latin3',
            '936', 'mac_turkish', 'big5hkscs', 'uhc', 'ksc5601', 'ibm424',
            'mac_latin2', 'euc_jis_2004', 'ibm500', 'cp936', 'cp862', 'latin10',
            'iso2022_jp_3', 'iso2022_jp_2', 'iso2022_jp_1', 'iso_2022_kr',
            'maccentraleurope', 'eucjisx0213', 'gbk', 'ibm857', 'iso8859_7',
            'ibm855', 'euckr', 'l2', 'ibm852', 'ibm850', 'cp950', 'ibm858',
            'utf_16be', '862', 'iso2022_jp_2004', 'latin', 'gb18030_2000',
            'sjis', 'iso_2022_jp_2', 'ebcdic_cp_he', 'ibm437', 'csbig5',
            'cp1361', 'maciceland', 'csptcp154', 'big5', 'sjis2004',
            'cyrillic_asian', 'l6', 'iso2022jp', 'l7', 'euc_jisx0213', 'l10',
            'l4', 'macturkish', 'korean', 'shiftjisx0213', 'l5', 'u32',
            'mac_iceland', 'unicode_1_1_utf_7', 'shift_jisx0213', 'ms950',
            'utf_32le', 'l3', 'gb2312_1980', 'iso2022_jp', 'hzgb', 'sjisx0213',
            'ms1361', 'csiso58gb231280', 'l1', 'iso_ir_58', 'u16', 'ms932',
            's_jisx0213', 'iso8859_4', 'ksx1001', 'euc_kr', 'ks_c_5601', 'u8',
            'ibm039', 'johab', 'greek8', 'iso8859_6', 'ptcp154', 'iso2022kr',
            'utf_32_be', 'ms949', 'ibm037', 'ms_kanji', 'cp850', 'shift_jis',
            'cp852', 'cp855', 'l8', 'cp857', 'cp856', 'cp775', 'iso2022jp_ext',
            'l9', 'jisx0213', 'hkscs', 'latin_1', 'us_ascii', 'iso_2022_jp_ext',
            'cp1026', 'cp_is', 'cp1252', 'iso2022jp_1', 'iso2022jp_3',
            'iso2022jp_2', 'shiftjis', 'utf_32', 'ujis', 'mac_cyrillic',
            'maclatin2', 'csiso2022kr', 'iso8859_16', '855', '857', '850',
            'ks_c_5601_1987', '852', 'ms936', 'u7', 'iso_8859_8', '858',
            'utf_16_be', 'cp1258', 'windows_1258', 'utf_16_le', 'windows_1254',
            'windows_1255', 'big5_tw', 'windows_1257', 'windows_1250',
            'windows_1251', 'windows_1252', 'windows_1253', 'hz', 'utf_8',
            'csshiftjis', 'ibm869', 'ibm866', 'mac_greek', 'ibm864', 'ibm865',
            'ibm862', 'ibm863', 'ibm860', 'ibm861', 'utf_8_sig', 'iso_8859_1',
            'ks_x_1001', 'cp949', 'pt154', 'windows_1256', 'utf32', '869',
            'utf', 'cp_gr', 'hz_gb_2312', '861', '860', '863', 'cp737', '865',
            'sjis_2004', '866', 'u_jis', 'iso8859_9', 'iso8859_8', 'iso8859_5',
            'iso2022_kr', 'cp875', 'cp874', 'iso8859_1', 'iso8859_3',
            'iso8859_2', 'gb18030', 'cp819', 'iso_8859_9', 'euccn',
            'iso_8859_7', 'iso_8859_6', 'iso_8859_5', 'iso_8859_4',
            'iso_8859_3', 'iso_8859_2', 'cp1006', 'gb2312', 'shift_jis_2004',
            'utf_32_le', 'eucgb2312_cn', 'hebrew', 'arabic', 'ascii',
            'mac_roman', 'iso8859_15', 'iso8859_14', 'hz_gb', 'iso8859_10',
            'iso8859_13', 'cp720', '950', 'koi8_u', 'utf16', 'utf_16', 'cp869',
            'iso_8859_15', 'iso_8859_14', 'iso_8859_13', 'iso2022jp_2004',
            'iso_8859_10', 'cp860', 'cp861', 'ebcdic_cp_be', 'cp863', 'cp864',
            'cp865', 'cp866', 'cp154', 'iso_2022_jp_3', 'shiftjis2004', '646',
            'ebcdic_cp_ch', 'cp1255', 'cp1254', 'cp1257', 'cp1256', 'cp1251',
            'cp1250', 'cp1253', '437', 'cp437', 'ibm775', 'big5_hkscs',
            'csiso2022jp', 'gb2312_80', 'latin4', 'latin5', 'latin6', 'latin7',
            'latin1', 'latin2', '949', 'macroman', 'utf_16le', 'cyrillic',
            'latin8', 'latin9', 'koi8_r', 'greek', '8859', 'cp037', 'euc_cn',
            'iso2022_jp_ext', 'utf_32be', 'cp858']

    @staticmethod
    def get_available_encodings_with_title():
        return [
            [_('ascii [English]'), 'ascii'],
            #[_('646 [English]'), 'ascii'],
            #[_('us-ascii [English]'), 'ascii'],
            [_('big5 [Traditional Chinese]'), 'big5'],
            #[_('big5-tw [Traditional Chinese]'), 'big5'],
            #[_('csbig5 [Traditional Chinese]'), 'big5'],
            #[_('big5hkscs [Traditional Chinese]'), 'big5hkscs'],
            [_('big5-hkscs [Traditional Chinese]'), 'big5hkscs'],
            #[_('hkscs [Traditional Chinese]'), 'big5hkscs'],
            #[_('cp037 [English]'), 'cp037'],
            [_('IBM037 [English]'), 'cp037'],
            #[_('IBM039 [English]'), 'cp037'],
            #[_('cp424 [Hebrew]'), 'cp424'],
            #[_('EBCDIC-CP-HE [Hebrew]'), 'cp424'],
            [_('IBM424 [Hebrew]'), 'cp424'],
            #[_('cp437 [English]'), 'cp437'],
            #[_('437 [English]'), 'cp437'],
            [_('IBM437 [English]'), 'cp437'],
            #[_('cp500 [Western Europe]'), 'cp500'],
            #[_('EBCDIC-CP-BE [Western Europe]'), 'cp500'],
            #[_('EBCDIC-CP-CH [Western Europe]'), 'cp500'],
            [_('IBM500 [Western Europe]'), 'cp500'],
            [_('cp720 [Arabic]'), 'cp720'],
            [_('cp737 [Greek]'), 'cp737'],
            #[_('cp775 [Baltic languages]'), 'cp775'],
            [_('IBM775 [Baltic languages]'), 'cp775'],
            #[_('cp850 [Western Europe]'), 'cp850'],
            #[_('850 [Western Europe]'), 'cp850'],
            [_('IBM850 [Western Europe]'), 'cp850'],
            #[_('cp852 [Central and Eastern Europe]'), 'cp852'],
            #[_('852 [Central and Eastern Europe]'), 'cp852'],
            [_('IBM852 [Central and Eastern Europe]'), 'cp852'],
            #[_('cp855 [Bulgarian, Byelorussian, Macedonian, Russian, 
            #Serbian]'), 'cp855'],
            #[_('855 [Bulgarian, Byelorussian, Macedonian, Russian, 
            #Serbian]'), 'cp855'],
            [_('IBM855 [Bulgarian, Byelorussian, Macedonian, Russian, Serbian]'
             ), 'cp855'],
            [_('cp856 [Hebrew]'), 'cp856'],
            #[_('cp857 [Turkish]'), 'cp857'],
            #[_('857 [Turkish]'), 'cp857'],
            [_('IBM857 [Turkish]'), 'cp857'],
            #[_('cp858 [Western Europe]'), 'cp858'],
            #[_('858 [Western Europe]'), 'cp858'],
            [_('IBM858 [Western Europe]'), 'cp858'],
            #[_('cp860 [Portuguese]'), 'cp860'],
            #[_('860 [Portuguese]'), 'cp860'],
            [_('IBM860 [Portuguese]'), 'cp860'],
            #[_('cp861 [Icelandic]'), 'cp861'],
            #[_('861 [Icelandic]'), 'cp861'],
            #[_('CP-IS [Icelandic]'), 'cp861'],
            [_('IBM861 [Icelandic]'), 'cp861'],
            #[_('cp862 [Hebrew]'), 'cp862'],
            #[_('862 [Hebrew]'), 'cp862'],
            [_('IBM862 [Hebrew]'), 'cp862'],
            #[_('cp863 [Canadian]'), 'cp863'],
            #[_('863 [Canadian]'), 'cp863'],
            [_('IBM863 [Canadian]'), 'cp863'],
            #[_('cp864 [Arabic]'), 'cp864'],
            [_('IBM864 [Arabic]'), 'cp864'],
            #[_('cp865 [Danish, Norwegian]'), 'cp865'],
            #[_('865 [Danish, Norwegian]'), 'cp865'],
            [_('IBM865 [Danish, Norwegian]'), 'cp865'],
            #[_('cp866 [Russian]'), 'cp866'],
            #[_('866 [Russian]'), 'cp866'],
            [_('IBM866 [Russian]'), 'cp866'],
            #[_('cp869 [Greek]'), 'cp869'],
            #[_('869 [Greek]'), 'cp869'],
            #[_('CP-GR [Greek]'), 'cp869'],
            [_('IBM869 [Greek]'), 'cp869'],
            [_('cp874 [Thai]'), 'cp874'],
            [_('cp875 [Greek]'), 'cp875'],
            #[_('cp932 [Japanese]'), 'cp932'],
            #[_('932 [Japanese]'), 'cp932'],
            #[_('ms932 [Japanese]'), 'cp932'],
            #[_('mskanji [Japanese]'), 'cp932'],
            [_('ms-kanji [Japanese]'), 'cp932'],
            #[_('cp949 [Korean]'), 'cp949'],
            #[_('949 [Korean]'), 'cp949'],
            [_('ms949 [Korean]'), 'cp949'],
            #[_('uhc [Korean]'), 'cp949'],
            #[_('cp950 [Traditional Chinese]'), 'cp950'],
            #[_('950 [Traditional Chinese]'), 'cp950'],
            [_('ms950 [Traditional Chinese]'), 'cp950'],
            [_('cp1006 [Urdu]'), 'cp1006'],
            #[_('cp1026 [Turkish]'), 'cp1026'],
            [_('ibm1026 [Turkish]'), 'cp1026'],
            #[_('cp1140 [Western Europe]'), 'cp1140'],
            [_('ibm1140 [Western Europe]'), 'cp1140'],
            #[_('cp1250 [Central and Eastern Europe]'), 'cp1250'],
            [_('windows-1250 [Central and Eastern Europe]'), 'cp1250'],
            #[_('cp1251 [Bulgarian, Byelorussian,Macedonian, Russian, 
            #Serbian]'), 'cp1251'],
            [_('windows-1251 [Bulgarian, Byelorussian,Macedonian, Russian, Serb'
               'ian]'), 'cp1251'],
            #[_('cp1252 [Western Europe]'), 'cp1252'],
            [_('windows-1252 [Western Europe]'), 'cp1252'],
            #[_('cp1253 [Greek]'), 'cp1253'],
            [_('windows-1253 [Greek]'), 'cp1253'],
            #[_('cp1254 [Turkish]'), 'cp1254'],
            [_('windows-1254 [Turkish]'), 'cp1254'],
            #[_('cp1255 [Hebrew]'), 'cp1255'],
            [_('windows-1255 [Hebrew]'), 'cp1255'],
            #[_('cp1256 [Arabic]'), 'cp1256'],
            [_('windows-1256 [Arabic]'), 'cp1256'],
            #[_('cp1257 [Baltic languages]'), 'cp1257'],
            [_('windows-1257 [Baltic languages]'), 'cp1257'],
            #[_('cp1258 [Vietnamese]'), 'cp1258'],
            [_('windows-1258 [Vietnamese]'), 'cp1258'],
            [_('euc_jp [Japanese]'), 'euc_jp'],
            #[_('eucjp [Japanese]'), 'euc_jp'],
            #[_('ujis [Japanese]'), 'euc_jp'],
            #[_('u-jis [Japanese]'), 'euc_jp'],
            [_('euc_jis_2004 [Japanese]'), 'euc_jis_2004'],
            #[_('jisx0213 [Japanese]'), 'euc_jis_2004'],
            #[_('eucjis2004 [Japanese]'), 'euc_jis_2004'],
            [_('euc_jisx0213 [Japanese]'), 'euc_jisx0213'],
            #[_('eucjisx0213 [Japanese]'), 'euc_jisx0213'],
            [_('euc_kr [Korean]'), 'euc_kr'],
            #[_('euckr [Korean]'), 'euc_kr'],
            #[_('korean [Korean]'), 'euc_kr'],
            #[_('ksc5601 [Korean]'), 'euc_kr'],
            #[_('ks_c-5601 [Korean]'), 'euc_kr'],
            #[_('ks_c-5601-1987 [Korean]'), 'euc_kr'],
            #[_('ksx1001 [Korean]'), 'euc_kr'],
            #[_('ks_x-1001 [Korean]'), 'euc_kr'],
            [_('gb2312 [Simplified Chinese]'), 'gb2312'],
            #[_('chinese [Simplified Chinese]'), 'gb2312'],
            #[_('csiso58gb231280 [Simplified Chinese]'), 'gb2312'],
            #[_('euc-cn [Simplified Chinese]'), 'gb2312'],
            #[_('euccn [Simplified Chinese]'), 'gb2312'],
            #[_('eucgb2312-cn [Simplified Chinese]'), 'gb2312'],
            #[_('gb2312-1980 [Simplified Chinese]'), 'gb2312'],
            #[_('gb2312-80 [Simplified Chinese]'), 'gb2312'],
            #[_('iso-ir-58 [Simplified Chinese]'), 'gb2312'],
            #[_('gbk [Unified Chinese]'), 'gbk'],
            #[_('936 [Unified Chinese]'), 'gbk'],
            #[_('cp936 [Unified Chinese]'), 'gbk'],
            [_('ms936 [Unified Chinese]'), 'gbk'],
            [_('gb18030 [Unified Chinese]'), 'gb18030'],
            #[_('gb18030-2000 [Unified Chinese]'), 'gb18030'],
            [_('hz [Simplified Chinese]'), 'hz'],
            #[_('hzgb [Simplified Chinese]'), 'hz'],
            #[_('hz-gb [Simplified Chinese]'), 'hz'],
            #[_('hz-gb-2312 [Simplified Chinese]'), 'hz'],
            #[_('iso2022_jp [Japanese]'), 'iso2022_jp'],
            #[_('csiso2022jp [Japanese]'), 'iso2022_jp'],
            #[_('iso2022jp [Japanese]'), 'iso2022_jp'],
            #[_('iso-2022-jp [Japanese]'), 'iso2022_jp'],
            #[_('iso2022_jp_1 [Japanese]'), 'iso2022_jp_1'],
            #[_('iso2022jp-1 [Japanese]'), 'iso2022_jp_1'],
            [_('iso-2022-jp-1 [Japanese]'), 'iso2022_jp_1'],
            #[_('iso2022_jp_2 [Japanese, Korean, Simplified Chinese, Wes
            #tern Europe, Greek]'), 'iso2022_jp_2'],
            #[_('iso2022jp-2 [Japanese, Korean, Simplified Chinese, West
            #ern Europe, Greek]'), 'iso2022_jp_2'],
            [_('iso-2022-jp-2 [Japanese, Korean, Simplified Chinese, Western Eu'
               'rope, Greek]'), 'iso2022_jp_2'],
            #[_('iso2022_jp_2004 [Japanese]'), 'iso2022_jp_2004'],
            #[_('iso2022jp-2004 [Japanese]'), 'iso2022_jp_2004'],
            [_('iso-2022-jp-2004 [Japanese]'), 'iso2022_jp_2004'],
            #[_('iso2022_jp_3 [Japanese]'), 'iso2022_jp_3'],
            #[_('iso2022jp-3 [Japanese]'), 'iso2022_jp_3'],
            [_('iso-2022-jp-3 [Japanese]'), 'iso2022_jp_3'],
            #[_('iso2022_jp_ext [Japanese]'), 'iso2022_jp_ext'],
            #[_('iso2022jp-ext [Japanese]'), 'iso2022_jp_ext'],
            [_('iso-2022-jp-ext [Japanese]'), 'iso2022_jp_ext'],
            #[_('iso2022_kr [Korean]'), 'iso2022_kr'],
            #[_('csiso2022kr [Korean]'), 'iso2022_kr'],
            #[_('iso2022kr [Korean]'), 'iso2022_kr'],
            [_('iso-2022-kr [Korean]'), 'iso2022_kr'],
            #[_('latin_1 [West Europe]'), 'latin_1'],
            #[_('iso-8859-1 [West Europe]'), 'latin_1'],
            #[_('iso8859-1 [West Europe]'), 'latin_1'],
            #[_('8859 [West Europe]'), 'latin_1'],
            #[_('cp819 [West Europe]'), 'latin_1'],
            #[_('latin [West Europe]'), 'latin_1'],
            [_('latin1 [West Europe]'), 'latin_1'],
            #[_('L1 [West Europe]'), 'latin_1'],
            #[_('iso8859_2 [Central and Eastern Europe]'), 'iso8859_2'],
            #[_('iso-8859-2 [Central and Eastern Europe]'), 
            #'iso8859_2'],
            [_('latin2 [Central and Eastern Europe]'), 'iso8859_2'],
            #[_('L2 [Central and Eastern Europe]'), 'iso8859_2'],
            #[_('iso8859_3 [Esperanto, Maltese]'), 'iso8859_3'],
            #[_('iso-8859-3 [Esperanto, Maltese]'), 'iso8859_3'],
            [_('latin3 [Esperanto, Maltese]'), 'iso8859_3'],
            #[_('L3 [Esperanto, Maltese]'), 'iso8859_3'],
            #[_('iso8859_4 [Baltic languages]'), 'iso8859_4'],
            #[_('iso-8859-4 [Baltic languages]'), 'iso8859_4'],
            [_('latin4 [Baltic languages]'), 'iso8859_4'],
            #[_('L4 [Baltic languages]'), 'iso8859_4'],
            #[_('iso8859_5 [Bulgarian, Byelorussian, Macedonian, 
            #Russian, Serbian]'), 'iso8859_5'],
            #[_('iso-8859-5 [Bulgarian, Byelorussian, Macedonian, 
            #Russian, Serbian]'), 'iso8859_5'],
            [_('cyrillic [Bulgarian, Byelorussian, Macedonian, Russian, Serbian'
               ']'), 'iso8859_5'],
            #[_('iso8859_6 [Arabic]'), 'iso8859_6'],
            #[_('iso-8859-6 [Arabic]'), 'iso8859_6'],
            [_('arabic [Arabic]'), 'iso8859_6'],
            #[_('iso8859_7 [Greek]'), 'iso8859_7'],
            #[_('iso-8859-7 [Greek]'), 'iso8859_7'],
            [_('greek [Greek]'), 'iso8859_7'],
            #[_('greek8 [Greek]'), 'iso8859_7'],
            #[_('iso8859_8 [Hebrew]'), 'iso8859_8'],
            #[_('iso-8859-8 [Hebrew]'), 'iso8859_8'],
            [_('hebrew [Hebrew]'), 'iso8859_8'],
            #[_('iso8859_9 [Turkish]'), 'iso8859_9'],
            #[_('iso-8859-9 [Turkish]'), 'iso8859_9'],
            [_('latin5 [Turkish]'), 'iso8859_9'],
            #[_('L5 [Turkish]'), 'iso8859_9'],
            #[_('iso8859_10 [Nordic languages]'), 'iso8859_10'],
            #[_('iso-8859-10 [Nordic languages]'), 'iso8859_10'],
            [_('latin6 [Nordic languages]'), 'iso8859_10'],
            #[_('L6 [Nordic languages]'), 'iso8859_10'],
            #[_('iso8859_13 [Baltic languages]'), 'iso8859_13'],
            #[_('iso-8859-13 [Baltic languages]'), 'iso8859_13'],
            [_('latin7 [Baltic languages]'), 'iso8859_13'],
            #[_('L7 [Baltic languages]'), 'iso8859_13'],
            #[_('iso8859_14 [Celtic languages]'), 'iso8859_14'],
            #[_('iso-8859-14 [Celtic languages]'), 'iso8859_14'],
            [_('latin8 [Celtic languages]'), 'iso8859_14'],
            #[_('L8 [Celtic languages]'), 'iso8859_14'],
            #[_('iso8859_15 [Western Europe]'), 'iso8859_15'],
            #[_('iso-8859-15 [Western Europe]'), 'iso8859_15'],
            [_('latin9 [Western Europe]'), 'iso8859_15'],
            #[_('L9 [Western Europe]'), 'iso8859_15'],
            #[_('iso8859_16 [South-Eastern Europe]'), 'iso8859_16'],
            #[_('iso-8859-16 [South-Eastern Europe]'), 'iso8859_16'],
            [_('latin10 [South-Eastern Europe]'), 'iso8859_16'],
            #[_('L10 [South-Eastern Europe]'), 'iso8859_16'],
            #[_('johab [Korean]'), 'johab'],
            #[_('cp1361 [Korean]'), 'johab'],
            [_('ms1361 [Korean]'), 'johab'],
            [_('koi8_r [Russian]'), 'koi8_r'],
            [_('koi8_u [Ukrainian]'), 'koi8_u'],
            [_('mac_cyrillic [Bulgarian, Byelorussian, Macedonian, Russian, Ser'
               'bian]'), 'mac_cyrillic'],
            #[_('maccyrillic [Bulgarian, Byelorussian, Macedonian, Russi
            #an, Serbian]'), 'mac_cyrillic'],
            [_('mac_greek [Greek]'), 'mac_greek'],
            #[_('macgreek [Greek]'), 'mac_greek'],
            [_('mac_iceland [Icelandic]'), 'mac_iceland'],
            #[_('maciceland [Icelandic]'), 'mac_iceland'],
            [_('mac_latin2 [Central and Eastern Europe]'), 'mac_latin2'],
            #[_('maclatin2 [Central and Eastern Europe]'), 'mac_latin2'],
            #[_('maccentraleurope [Central and Eastern Europe]'), 'mac_l
            #atin2'],
            [_('mac_roman [Western Europe]'), 'mac_roman'],
            #[_('macroman [Western Europe]'), 'mac_roman'],
            [_('mac_turkish [Turkish]'), 'mac_turkish'],
            #[_('macturkish [Turkish]'), 'mac_turkish'],
            #[_('ptcp154 [Kazakh]'), 'ptcp154'],
            #[_('csptcp154 [Kazakh]'), 'ptcp154'],
            #[_('pt154 [Kazakh]'), 'ptcp154'],
            #[_('cp154 [Kazakh]'), 'ptcp154'],
            [_('cyrillic-asian [Kazakh]'), 'ptcp154'],
            [_('shift_jis [Japanese]'), 'shift_jis'],
            #[_('csshiftjis [Japanese]'), 'shift_jis'],
            #[_('shiftjis [Japanese]'), 'shift_jis'],
            #[_('sjis [Japanese]'), 'shift_jis'],
            #[_('s_jis [Japanese]'), 'shift_jis'],
            [_('shift_jis_2004 [Japanese]'), 'shift_jis_2004'],
            #[_('shiftjis2004 [Japanese]'), 'shift_jis_2004'],
            #[_('sjis_2004 [Japanese]'), 'shift_jis_2004'],
            #[_('sjis2004 [Japanese]'), 'shift_jis_2004'],
            [_('shift_jisx0213 [Japanese]'), 'shift_jisx0213'],
            #[_('shiftjisx0213 [Japanese]'), 'shift_jisx0213'],
            #[_('sjisx0213 [Japanese]'), 'shift_jisx0213'],
            #[_('s_jisx0213 [Japanese]'), 'shift_jisx0213'],
            [_('utf_32 [all languages]'), 'utf_32'],
            #[_('U32 [all languages]'), 'utf_32'],
            #[_('utf32 [all languages]'), 'utf_32'],
            #[_('utf_32_be [all languages]'), 'utf_32_be'],
            [_('UTF-32BE [all languages]'), 'utf_32_be'],
            #[_('utf_32_le [all languages]'), 'utf_32_le'],
            [_('UTF-32LE [all languages]'), 'utf_32_le'],
            [_('utf_16 [all languages]'), 'utf_16'],
            #[_('U16 [all languages]'), 'utf_16'],
            #[_('utf16 [all languages]'), 'utf_16'],
            #[_('utf_16_be [all languages (BMP only)]'), 'utf_16_be'],
            [_('UTF-16BE [all languages (BMP only)]'), 'utf_16_be'],
            #[_('utf_16_le [all languages (BMP only)]'), 'utf_16_le'],
            [_('UTF-16LE [all languages (BMP only)]'), 'utf_16_le'],
            [_('utf_7 [all languages]'), 'utf_7'],
            #[_('U7 [all languages]'), 'utf_7'],
            #[_('unicode-1-1-utf-7 [all languages]'), 'utf_7'],
            [_('utf_8 [all languages]'), 'utf_8'],
            #[_('U8 [all languages]'), 'utf_8'],
            #[_('UTF [all languages]'), 'utf_8'],
            #[_('utf8 [all languages]'), 'utf_8'],
            [_('utf_8_sig [all languages]'), 'utf_8_sig']
        ]
