import pandas as pd
import numpy as np
import time
import json
import glob
import tarfile
import StringIO
import cStringIO
import sys
# import gzip

# Use this file like:
# python CrowdParser.py ../data/validate/JSON-User34-Base

# v0.48 Now taking in directory info when activating script so it no longer
#       needs to be copied into the data folder and run locally <3

# v0.49 Fixed the tarfile names that were being written so that it has '_'
#       between the type of tar file (phone_gyro, or whatever)

# v0.50 Add self.device_type so we can keep track if we're working on phone or
#       watch files. Then make the path for loop two times in the primary
#       run_me method.
#
#       Modified run_me method so that it calls walk_file_lists, first with
#       the watch_file_paths, then with the phone_file_paths

# v0.51 Fixed bug in self.device_type because watch is now first since it's
#       smaller than the phone data.

class CrowdParser(object):

    def __init__(self, path, cache_max=100):
        '''
        Create class object:
        '''

        # set the max size of the file caches. might need to be tuned but prob not
        self.cache_max = cache_max

        self._path = path

        # put gyroscope_uncalibrated before gyroscope to prevent searching
        # for gyroscape first adding uncalibrated and calibrated to the same
        # tar file
        #
        # Make sure default is last so if we don't find a valid file then
        # add it to the default (something probably went wrong if there's
        # anything in default.tar)
        self.file_types = ["accelerometer", "applications", "battery", "gravity",
                    "gyroscope_uncalibrated", "gyroscope", "light",
                    "linear_acceleration", "magnetometer", "network_traffic",
                    "pressure", "proximity", "rotation_vector", "screen",
                    "sensor_metadata", "step_counter", "wlan-alias",
                    "connectivity-alias", "cell-alias", "connection_strength",
                    "default",]

        # because the mobile data file formatting is not consistent :-(
        self.fixed_file_types = ["accelerometer", "applications", "battery", "gravity",
                    "gyroscope_uncalibrated", "gyroscope", "light",
                    "linear_acceleration", "magnetometer", "network_traffic",
                    "pressure", "proximity", "rotation_vector", "screen",
                    "sensor_metadata", "step_counter", "wlan_alias",
                    "connectivity_alias", "cell_alias", "connection_strength",
                    "default"]

        self.num_types = len(self.file_types)  # number of file types so we don't have
                                        # to keep calling over and over

        # make a list of lists to cache files so they can be written in batches
        # to speed things up by ~100x
        self.file_cache = [[] for x in range(self.num_types)]

        # keep track if we need to write a file or append to it
        self.cache_writes = [0 for x in range(self.num_types)]

        # run this locally as a crappy simplification
        _path = "*.json"

        self.phone_file_paths = glob.glob(self._path + "/phone/*.json")
        self.watch_file_paths = glob.glob(self._path + "/watch/*.json")

        # keep track if working on phone or watch stuff
        self.device_type = "watch"

        self.all_time = time.time()

    def run_me(self):
        '''
        Runs walk file_lists for watch then phone directories
        '''
        self.walk_file_lists(self.watch_file_paths)

        self.walk_file_lists(self.phone_file_paths)


    def walk_file_lists(self, list_of_files):
        '''
        Attempts to fix all of the timestamps in all of the json files
        then save those file to a tar of the proper category
        350 files 86.4s
        '''

        for idx, _file in enumerate(list_of_files):

            # print _file
            # ../data/trial/JSON-User34-Base/phone/c-screen-16112016-003928-857.json
            # ../data/trial/JSON-User34-Base/phone/fixed/tfxd-c-screen-16112016-003928-857.json

            start_time = time.time()
            # get a list of time offset dataframes so we can write them out to one
            # .json next
            data = self.fix_file_in_json(_file)

            json_str, _size = self.list_to_file_stream(data)

            run_time = time.time() - self.all_time
            file_time = time.time() - start_time
            print "File#: {:0>5d} Total t(s):{:6.2f} t(s):{:2.2f} file: {:>25}".format(idx, run_time, file_time, _file)

            # add idx to add_to_cache so that we can reference the fixed file list
            self.add_to_cache(_file, json_str, _size)

        # empty all of the remaining caches
        for idx in range(self.num_types):
            self.write_cache(idx)

        self.device_type = "watch"

    def write_file(self, _path, mode, data_list):
        '''
        Writes or appends giving the provided data
        _path is the path and filename
        mode is "w" or "a" for creating file or appending to file
        data_list is a list of tuples that contains the data to be written
        '''
        # open the file in the requested
        with tarfile.open(_path, mode) as tar_out:

            for _file in data_list:
                info = tar_out.tarinfo("tfxd-" + _file[0])

                # set the size to the len of the StringIO obj
                info.size = _file[2]

                # actually write the file
                tar_out.addfile(info, _file[1])

            print "    Wrote to " + _path


    def write_cache(self, index):
        '''
        Write out the provided cache of json files.  If count is 0 then make a new
        file, otherwise append to existing file.  File written is at _path.
        Explicitly check if it is a new file to make a new file. Python might
        just be ok implicitly creating a new file even in append mode if that
        file doesn't already exist.
        However, what we want to avoid is appending to a file that exists from
        a previous run. Therefore explicitly write (overwrite) the file at the
        start of the run so we avoid this issue.
        '''

        # path will be the same if the file is new or appended
        # add device_type into the mix so it can handle phone and watch stuff
        _path = self._path + "/" + self.device_type + "_" + self.fixed_file_types[index] + ".tar"

        if self.cache_writes[index] == 0:   # create the file

            self.write_file(_path, "w", self.file_cache[index])

            self.cache_writes[index] = 1    # increment the file writes in
                                            # order to append next time

        else:
            self.write_file(_path, "a", self.file_cache[index])

        # reset the list for this cache
        self.file_cache[index] = []

    def add_to_cache(self, _file, json_str, _size):
        '''
        Using _file figure out which cache to add the file to and then append
        the tuple of data to the proper list.
        Then check the length of the list to be sure that the cache hasn't
        grown too large.
        If the cache of this particular index is too large then call a method
        to write it out.
        '''

        for idx in range(self.num_types):
            if self.file_types[idx] in _file:   # if the file type in file name

                # add the current data to the list at the proper index
                self.file_cache[idx].append((_file, json_str, _size))

                # if the cache is now larger than the max write it out
                if len(self.file_cache[idx]) > self.cache_max:
                    self.write_cache(idx)

                return True # hacky way of avoiding a flag to indicate we didn't get a match

        # if we got this far then we must not have gotten a match. Add the file
        # to the default index
        idx = self.num_types - 1
        self.file_cache[idx].append((_file, json_str, _size))

        # if the cache is now larger than the max write it out
        if len(self.file_cache[idx]) > self.cache_max:
            self.write_cache(idx)

    def list_to_file_stream(self, df_dict):
        '''
        Takes in a dictionary of data frames that have been timestamp corrected.
        Turns dataframe into StringIO object
        Returns:
        StringIO object representing a json file created with the above list
        length of data
        tuple like: (file_string, len)
        '''

        _length = len(df_dict)

        # handling the file in memory so caching/write outs aren't necessary
        # anymore.  Still need some kind of list that stores the intermediary
        # data which will ultimately be converted to StringIO.  Later
        # might want to make this a set object instead of list as it would
        # prob speed things up.  For now just get it working
        # TODO: convert to set?
        write_cache = []

        for idx in xrange(_length):

            # get JSON data as a string and write it to the file
            jstring = json.dumps(df_dict[idx])

            # if this is the first item then prepend the string with a bracket
            if idx == 0:
                jstring = "[" + jstring

            # check to see if we're on the last dataframe.  If so close with
            # ']' instead of ','
            if idx < _length - 1:
                jstring = jstring + ","
            # at the end, close the bracket
            else:
                jstring = jstring + "]"

            # add string to the write_cache
            write_cache.append(jstring)

        temp_string = '\n'.join(write_cache)
        _len = len(temp_string)
        file_string = cStringIO.StringIO(temp_string)

        return file_string, _len

    def fix_file_in_json(self, _file):
        '''
        use the path provided to read in JSON file
        apply time correction to time fields in JSON file
        return list of fixed data frames as a valid JSON file
        '''
        # using a set is not possible because data frames are mutable
        # using a dictionary is mostly a waste of time because the
        # size of the lists are mostly small (less than 100)
        processed_data_list = []

        # print self._path + _file

        # parse the filename to get the time
        file_time = self.filename_to_time(_file)

        with open(_file) as raw_data:

            raw_lines = raw_data.readlines()

            for line in raw_lines:
                # read in the file line as a json object
                jdata = json.loads(line)

                offset = self.determine_time_correction_offset(file_time, jdata["timestamp"][0])

                jdata = self.apply_offset_to_json(jdata, offset)

                processed_data_list.append(jdata)

        return processed_data_list

    def determine_time_correction_offset(self, true_time, drifted_time):
        '''
        Determine how much the 'bad_time' needs to be adjusted in order
        to be aligned to the 'true_time'. times provided as int/longs
        True time is provided in milliseconds and drifted_time is in nanoseconds
        It seems like the relative time is most important so maybe figure the
        offset to milliseconds and later when fixing times use nanoseconds
        One benefit is that window times should be round numbers. Also using
        nanosecond offsets sort of implies that level of precision absolute,
        which is probably misleading
        Returns: offset in milliseconds that will be applied to 'bad' times
        '''
        # convert drifted time to ms instead of ns
        drifted_time = np.int64(drifted_time/1000000.0)

        # attemp to verify that we're comparing numbers that are both of
        # equivalent time granularity
        if len(str(true_time)) == len(str(drifted_time)):
            return np.int64(true_time - drifted_time)
        else:
            print
            print "Time granularity is messed up:"
            print "true_time {} bad_time {}".format(true_time, drifted_time)
            return None

    def apply_offset_to_json(self, data, offset):
        '''
        Applies the correction time factor to the correct items in the dictionary
        Returns:
        updated data dictionary
        '''
        data["window_start"] += offset
        data["window_end"] += offset
        data["pane_start"] += offset
        data["pane_end"] += offset

        # try to fix all timestamps
        data["timestamp"] = [item + offset for item in data["timestamp"]]

        return data

    def filename_to_time(self, filename):
        '''
        Takes in a filename with the assumption that the last 3 fields seperated
        by '-' are pieces of a time stamp in date/time format.
        ex: c-wlan-alias-06102016-194105-676.json
        Returns:
        long integer value of nanoseconds by unix epoch
        '''

        # _f.split(".")[0]
        # c-connection_strength-06102016-133055-758

        # _f.split(".")[0].split("-")[-3:]
        # ['06102016', '133055', '758']

        # get the last 3 pieces of the file, we don't know for sure how many
        # pieces of the file name that there will be before these digits
        # so take the trailing ones
        time_strings = filename.split("/")[-1].split(".")[0].split("-")[-3:]

        # convert the pieces into a parsable format
        date = time_strings[0] + "_" + time_strings[1]
        # print date # 06102016_194105_676

        pattern = "%d%m%Y_%H%M%S"
        epoch = int(time.mktime(time.strptime(date, pattern)))

        # append milliseconds onto the calculated epoch
        # kind of a hack but since we're calculating once per json section shouldn't
        # be too bad
        # file_time = long( str(epoch) + time_strings[2]) * 1000000

        # since assuming ms time fidelity for writing the file don't multiply
        # by a million

        file_time = long( str(epoch) + time_strings[2])

        return file_time


def main():
    _path = sys.argv[1]

    print _path

    fix_files = CrowdParser(path=_path, cache_max=100)

    #
    fix_files.run_me()

if __name__ == "__main__":
    main()
