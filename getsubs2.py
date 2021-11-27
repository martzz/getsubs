#
# This file is part of the martzz/getsubs distribution (https://github.com/martzz/getsubs).
# Copyright (c) 2017 Martin Zouzelka.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

'''
Created on Oct 29, 2017

@author: Martin Zouzelka
'''

import argparse
import xmlrpclib
import struct
import StringIO
import gzip
import os
import sys


def acquire_subs(context):
    client = XmlRpcClient()
    
    if context.path:
        path = context.path
        _, file_name = os.path.split(path)
        file_size = os.path.getsize(context.path)
        
        # calculate movie hash
        movie_hash = HashCalculator.get_hash(path, file_size)
        print movie_hash
        
        # search and download subtitles using movie hash
        subtitles = client.get_subs_via_hash(context.lang, movie_hash, file_size)
        
        # save subtitles using the movie file name with _<lang> suffix (e.g. Aliens_eng.srt)
        m_name, _ = os.path.splitext(file_name)
        _, s_ext = os.path.splitext(subtitles.file_name) 
        sub_file_name = '{name}_{lang}{ext}'.format(name=m_name, lang=context.lang, ext=s_ext)
        subtitles.file_name = sub_file_name
        
        save_subs(subtitles, context.encoding, context.output_dir)
        
    else:
        # search and download subtitles using imdb id
        subtitles = client.get_subs_via_imdb(context.lang, context.imdb_id)
        
        # save subtitles with original name to actual dir
        save_subs(subtitles, context.encoding, context.output_dir)
            
    

def save_subs(subtitles, encoding, directory):
    if encoding:
        subtitles.convert_encoding(encoding)

    full_path = os.path.join(directory, subtitles.file_name)

    sub_file = open(full_path, 'w')
    sub_file.write(subtitles.data)
    sub_file.close()
    
    print "Subtitles saved to " + full_path
    
    
class HashCalculator:
    
    @staticmethod
    def get_hash(path, file_size):
        try:
            long_long_format = 'q'  # long long 
            byte_size = struct.calcsize(long_long_format) 
            f = file(path, "rb") 
            hash = file_size
            if file_size < 65536 * 2: 
                return "Cannot calculate movie hash: SizeError"
            for x in range(65536/byte_size): 
                buffer = f.read(byte_size) 
                (l_value,)= struct.unpack(long_long_format, buffer)  
                hash += l_value 
                hash = hash & 0xFFFFFFFFFFFFFFFF #to remain as 64bit number 
                 
            f.seek(max(0, file_size - 65536), 0) 
            for x in range(65536/byte_size): 
                buffer = f.read(byte_size) 
                (l_value,)= struct.unpack(long_long_format, buffer)  
                hash += l_value 
                hash = hash & 0xFFFFFFFFFFFFFFFF 
                
            f.close() 
            returned_hash =  "%016x" % hash 
            return returned_hash 
        except (IOError):
            return "Cannot calculate movie hash: IOError"        
    

class XmlRpcClient:
    """
    Establishes connection with opensubtitles.org and tries to search for subtitles (via hash and file size or imdb id).
    Subsequently the user is prompted to choose subtitles to download.
    """
    
    SERVER_URL= 'http://api.opensubtitles.org/xml-rpc'
    
    
    def __init__(self):
        self.__server = xmlrpclib.Server(self.SERVER_URL)
        self.__login = self.__server.LogIn('', '', 'en', 'GetSubs v2.0')
    
    def get_subs_via_hash(self, lang, file_hash, file_size):
        
        # the file size must be string, becuase size of bigger movies would exceed xml-rpc limit for int 
        search_pattern= {'sublanguageid': lang, 'moviehash': file_hash, 'moviebytesize': str(file_size)}
        return self.__get_subs(search_pattern)
    
    
    def get_subs_via_imdb(self, lang, imdb_id):
        search_pattern = {'sublanguageid': lang, 'imdbid': imdb_id}
        return self.__get_subs(search_pattern)
       
    
    
    def __get_subs(self, search_pattern):
        search_res = self.__server.SearchSubtitles(self.__login['token'], [search_pattern])
        
        if not search_res:
            self.__terminate_session("No subtitles found ..terminating")
            
        sub = self.__show_user_prompt(search_res)
        sub_data = self.__download_subs(sub)
        subtitles = Subtitles(sub['SubFileName'], sub['SubEncoding'], sub_data)
       
        self.__server.LogOut(self.__login)
        return subtitles  
            
            
    def __show_user_prompt(self, search_res):
        search_data = search_res['data']
        sub_count = len(search_data)
        
        print 'Found %d subtitle files' % sub_count
        print '---------------------------- SUBTITLES ------------------------------------'
        print '#%s%s' % (Constant.DELIMITER, Constant.DELIMITER.join(Constant.SUB_LIST_HEADER))
        
        i = 1
        for sub in search_data:
            
            data_list = []
            for field in Constant.SUB_LIST_FIELDS:
                data_list.append(sub[field])
                
            print '%d%s%s' % (i, Constant.DELIMITER, Constant.DELIMITER.join(data_list))
            i += 1    
            
        print '---------------------------------------------------------------------------'
            
        num = None
        while num is None or num > sub_count or num < 0:
            try:
                num = int(raw_input('Choose subtitles to download 0-%d (0 - nothing): ' % sub_count))
            except:
                continue
            
        if num == 0:
            self.__terminate_session("Terminating..")
            
        return search_data[num - 1]                
        
           
    
    def __download_subs(self, sub):
        print 'Downloading...%s' % sub['SubFileName']
        downloaded_sub = self.__server.DownloadSubtitles(self.__login['token'], [sub['IDSubtitleFile']])
        return self.__decompress_subs(downloaded_sub['data'][0]['data'])
        
        
    @staticmethod    
    def __decompress_subs(sub):
        stream = StringIO.StringIO(sub.decode('base64_codec'))
        gz = gzip.GzipFile(fileobj= stream)
        sub = gz.read()
            
        return sub
    

    def __terminate_session(self, message):
        print message
        self.__server.LogOut(self.__login)
        exit(0)


class Subtitles:
    
    def __init__(self, file_name, encoding, data):
        self.file_name = file_name
        self.encoding = encoding
        self.data = data
        
    def convert_encoding(self, target_encoding):
        d_data = self.data.decode(self.encoding)
        self.data = d_data.encode(target_encoding)        
            


class Constant:
    
    SUB_LIST_HEADER = ['Size', 'Lang', 'Enc', 'Sum CD', 'Act CD', 'Name']
    SUB_LIST_FIELDS = ['SubSize', 'LanguageName', 'SubEncoding', 'SubSumCD', 'SubActualCD', 'SubFileName']
    
    DELIMITER = "\t\t"
    
    def __init__(self):
        pass           

class Context:
    """
    Property holder
    """

    def __init__(self, args):
        print "Arguments: " + str(args)
        self.lang = args.language
        self.encoding = args.encoding
        self.path = args.path
        self.imdb_id = args.imdb_id
        
        self.output_dir = args.output_dir
        
        self.__validate()
        
    def __validate(self):
        if self.path and self.imdb_id:
            raise ValueError("Cannot specify path to the movie (hash based search) together with imdb id (imdb id based search)")



if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    
    parser.add_argument("output_dir", help="Path of the output directory.")
    parser.add_argument("-l", "--language", help="Subtitles language (e.g. eng, cze) - default english.")
    parser.add_argument("-e", "--encoding", help="Convert to a specific character encoding (e.g. utf-8, latin-1).")
    parser.add_argument("-p", "--path", help="Directory containing the movie (subtitle search using hash of the movie). " \
                        "Use this option to get correctly timed subtitles.")
    parser.add_argument("-i", "--imdb_id", help="Imdb id of the movie (subtitle search using imdb id). " \
                        "Imdb id could be obtained from the imdb.com url: https://www.imdb.com/title/tt2210497/ where 2210497 is the id.")
    
    context = Context(parser.parse_args())
    
    acquire_subs(context)

