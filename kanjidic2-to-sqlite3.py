#!/usr/bin/env python3

# Copyright (C)2015 Marcus Soll
#
# kanjidic2-to-sqlite3 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# kanjidic2-to-sqlite3 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kanjidic2-to-sqlite3. If not, see <http://www.gnu.org/licenses/>.

import sys
import os
import time
import sqlite3
import xml.etree.ElementTree
from PyQt4.QtCore import qAbs


def kanjidic2_to_sqlite3(input, output):
    """
    Transforms a KANJIDIC2-XML-file to a SQLite3-database
    :param input: Path to input XML file
    :type input: str
    :param output: Path to output SQLite3 file
    :type: output: str
    :return: None
    """
    print('Input file: %s' % input)
    print('Output file: %s' % output)

    if not os.path.isfile(input):
        raise IOError('Input file %s not found' % input)
        return

    if os.path.exists(output):
        raise IOError('Output file %s already exists' % output)
        return

    print('Converting...')

    #Counter
    converted = 0
    not_converted = 0

    #Connect to database
    connection = sqlite3.connect(output)
    cursor=connection.cursor()

    #Creating tables
    cursor.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
    cursor.execute("CREATE TABLE kanji (literal TEXT PRIMARY KEY, radical INT, strokecount INT, JLPT INT, ONreading TEXT, KUNreading TEXT, nanori TEXT, meaning TEXT, skip_1 INT, skip_2 INT, skip_3 INT)")
    connection.commit()

    #Creating metadata
    cursor.execute("INSERT INTO meta VALUES ('license', 'CC-BY-SA 4.0 International')")
    cursor.execute("INSERT INTO meta VALUES ('database date of creation', ?)", (time.strftime('%Y-%m-%d'),))

    #Parsing KANJIDIC2 xml
    element_tree = xml.etree.ElementTree.parse(input)
    root = element_tree.getroot()

    #Inserting metadata from KANJIDIC2
    for element in root.findall('header'):
        for header in element.iter():
            if header.tag == 'file_version':
                cursor.execute("INSERT INTO meta VALUES ('kanjidic2 file version', ?)", (header.text,))
            elif header.tag == 'database_version':
                cursor.execute("INSERT INTO meta VALUES ('kanjidic2 database version', ?)", (header.text,))
            elif header.tag == 'date_of_creation':
                cursor.execute("INSERT INTO meta VALUES ('kanjidic2 date of creation', ?)", (header.text,))
    connection.commit()

    for element in root.findall('character'):
        literal = ''
        radical = ''
        strokecount = ''
        JLPT = '0'
        ON = ''
        KUN = ''
        nanori = ''
        meaning = ''
        skip_1 = ''
        skip_2 = ''
        skip_3 = ''
        for value in element.iter():
            if value.tag == 'literal':
                literal = value.text
            elif value.tag == 'radical':
                for rad_value in value.iter():
                    if 'rad_type' in rad_value.attrib.keys() and rad_value.attrib['rad_type'] == 'classical':
                        radical = rad_value.text
            elif value.tag == 'misc':
                for misc in value.iter():
                    if misc.tag == 'stroke_count':
                        strokecount = misc.text
                    elif misc.tag == 'jlpt':
                        JLPT = misc.text
            elif value.tag == 'reading_meaning':
                for reading_meaning in value.iter():
                    if reading_meaning.tag == 'rmgroup':
                        for rmgroup in reading_meaning.iter():
                            if rmgroup.tag == 'reading' and 'r_type' in rmgroup.attrib.keys() and rmgroup.attrib['r_type'] == 'ja_on':
                                if ON != '':
                                    ON += ', '
                                ON += rmgroup.text
                            elif rmgroup.tag == 'reading' and 'r_type' in rmgroup.attrib.keys() and rmgroup.attrib['r_type'] == 'ja_kun':
                                if KUN != '':
                                    KUN += ', '
                                KUN += rmgroup.text
                            elif rmgroup.tag == 'meaning' and len(rmgroup.attrib) == 0:
                                if meaning != '':
                                    meaning += ', '
                                meaning += rmgroup.text
                    elif reading_meaning.tag == 'nanori':
                        if nanori != '':
                            nanori += ', '
                        nanori += reading_meaning.text
            elif value.tag == 'query_code':
                for q_code in value.iter():
                    if q_code.tag == 'q_code' and 'qc_type' in q_code.attrib.keys() and q_code.attrib['qc_type'] == 'skip' and 'skip_misclass' not in q_code.attrib.keys():
                        s = q_code.text
                        s = s.split('-')
                        skip_1 = s[0]
                        skip_2 = s[1]
                        skip_3 = s[2]

        if literal != '' and radical != '' and strokecount != '' and meaning != '':
                cursor.execute("INSERT INTO kanji VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (literal, radical, strokecount, JLPT, ON, KUN, nanori, meaning, skip_1, skip_2, skip_3))
                converted += 1
        else:
                not_converted +=1

    connection.commit()

    cursor.execute("CREATE TABLE radical (radical TEXT PRIMARY KEY, number INT)")

    for i in range(214):
        cursor.execute("INSERT INTO radical VALUES (?, ?)", (chr(0x2F00+i), i+1))

    connection.commit()
    connection.close()
    print('Converting done!')
    print('Converted Kanji: %i' % converted)
    print('Not converted Kanji: %i' % not_converted)
    return

#A simple starting wrapper
if __name__ == '__main__':
    if len(sys.argv[1:]) != 2:
        print('Please specify exactly two arguments:')
        print('- First the input KANJIDIC2 file')
        print('- Second the output SQLite3 file')
        sys.exit(0)

    try:
        kanjidic2_to_sqlite3(sys.argv[1], sys.argv[2])
    except KeyboardInterrupt:
        print('\nAborted')
        sys.exit(0)