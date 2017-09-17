#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""

import cv2
import numpy as np
from argparse import ArgumentParser
from simplejson import load
from os import system
from datetime import datetime, date, timedelta
try:
    from urllib.request import Request, urlopen  # Python 3
except ImportError:
    from urllib2 import Request, urlopen  # Python 2

__cloudcover__ = 15
__longitude__ = -70.881337
__latitude__ = 42.421546
__today__ = date.today()
__end_date__ = __today__.isoformat()
__start_date__ = (__today__ - timedelta(weeks=52)).isoformat()
__picker__ = 'date'
__out_file__ = 'out'


def parse_arguments(args=None):
    """
    Parse command-line arguments.
    """
    assert args is None or isinstance(args, list)
    # Parse command-line arguments
    parser = ArgumentParser(
        description="Fetch SkyWatch data for a particular target."
    )
    default_cloudcover = __cloudcover__
    parser.add_argument(
        '--cloudcover', '-c', default=default_cloudcover,
        nargs='?', type=int, const=default_cloudcover,
        help='The maximum allowed percentage of cloud cover. ' +
        'By default this is {}'.format(default_cloudcover)
    )
    default_longitude = __longitude__
    parser.add_argument(
        '--longitude', '-x', default=default_longitude,
        nargs='?', type=float, const=default_longitude,
        help='The target longitude. ' +
        'By default this is {}'.format(default_longitude)
    )
    default_latitude = __latitude__
    parser.add_argument(
        '--latitude', '-y', default=default_latitude,
        nargs='?', type=float, const=default_latitude,
        help='The target latitude. ' +
        'By default this is {}'.format(default_latitude)
    )
    default_start_date = __start_date__
    parser.add_argument(
        '--startdate', '-s', default=default_start_date,
        nargs='?', const=default_start_date,
        help='The search date range start. ' +
        'By default this is "{}"'.format(default_start_date)
    )
    default_end_date = __end_date__
    parser.add_argument(
        '--enddate', '-e', default=default_end_date,
        nargs='?', const=default_end_date,
        help='The search date range end. ' +
        'By default this is "{}"'.format(default_end_date)
    )
    parser.add_argument(
        '--apikey', '-a', required=True, nargs='?',
        help='The SkyWatch API key. There is no default.'
    )
    default_picker = __picker__
    parser.add_argument(
        '--picker', '-p', default=default_picker,
        nargs='?', const=default_picker,
        choices=["date", "resolution", "cloudcover"],
        help='The priority field for picking data; ' +
        'it can be "date", "resolution", or "cloudcover". ' +
        'By default this is "{}"'.format(default_picker)
    )
    default_output_file = __out_file__
    parser.add_argument(
        '--outfile', '-o', default=default_output_file,
        nargs='?', const=default_output_file,
        help='The output file name. ' +
        'By default this is "{}" '.format(default_output_file) +
        'and the extension ".jp2" will be automatically provided.'
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true', default=True,
        help='Make output more verbose, useful for debugging.'
    )
    return parser.parse_args(args)


def compare_for_larger(num1, num2):
    """
    Compare numbers favoring bigger.
    """
    return num1 > num2


def compare_for_smaller(num1, num2):
    """
    Compare numbers favoring smaller.
    """
    return num1 < num2


def extract_first_date(date_range_str):
    """
    Pull the first date out of a SkyWatch data record.
    """
    datetime_format = "%Y-%m-%dT%H:%M:%S.%f+00:00"
    return datetime.strptime(date_range_str[1:33], datetime_format)


def compare_first_dates(date1str, date2str):
    """
    Compare first dates for two SkyWatch data records.
    """
    return compare_for_larger(extract_first_date(date1str['time']),
                              extract_first_date(date2str['time']))


def metadata_fetch(latitude, longitude,
                   start_date, end_date,
                   cloudcover, info_headers):
    """
    Fetches the image metadata from SkyWatch.
    """
    info_url = "https://api.skywatch.co/data/time/{0},{1}".format(start_date,
                                                                  end_date) + \
               "/location/{0},{1}/cloudcover/{2}".format(longitude, latitude,
                                                         cloudcover) + \
               "/band/true-colour-image"
    request = Request(info_url)
    for header_name, header_data in info_headers.items():
        request.add_header(header_name, header_data)
    response = urlopen(request)
    if response.code == 200:
        info = load(response)
    else:
        print("Failed to download image metadata ({0}): {1}".format(
            response.code, response.reason))
        info = []
    return info


def image_fetch(image_metadata, info_headers, verbose=False):
    """
    Fetches the image itself from SkyWatch.
    """
    if verbose:
        print("Loading {0} byte image ({1} meter resolution)...".format(
            image_metadata['size'], image_metadata['resolution']))
    request = Request(image_metadata["download_path"])
    for header_name, header_data in info_headers.items():
        request.add_header(header_name, header_data)
    response = urlopen(request)
    if response.code == 200:
        image_data = response.read()
    else:
        image_data = None
        print("Failed to download image ({0}): {1}".format(
            response.code, response.reason))
    return image_data


def choose_and_fetch_image():
    """
    Figures out the best available image to get and gets it.
    """
    pickers = {
        'date': compare_first_dates,
        'resolution': compare_for_larger,
        'cloudcover': compare_for_smaller
    }
    args = parse_arguments()
    if args.verbose:
        print("Will be searching from {0} to {1} ".format(args.startdate,
                                                          args.enddate) +
              "for location ({0}, {1}) ".format(args.latitude,
                                                args.longitude) +
              "with maximum {0}% cloud cover ".format(args.cloudcover) +
              "(favoring {0}).".format(args.picker))
    info_headers = {
        "x-api-key": args.apikey
    }
    metadata = metadata_fetch(args.latitude, args.longitude,
                              args.startdate, args.enddate,
                              args.cloudcover, info_headers)
    picker_function = pickers[args.picker]
    if len(metadata) > 0:
        metadata.sort(picker_function)
        chosen_image = image_fetch(metadata[0], info_headers, args.verbose)
        # Store the image
        if args.verbose:
            "Saving file..."
        try:
            with open(args.outfile + '.jp2', 'wb') as output_image_file:
                output_image_file.write(chosen_image)
        except IOError as err:
            print("Trouble saving file: {0}".format(str(err)))
            filename = None
        filename = args.outfile
    else:
        filename = None
        print("No matching image found.")
    if args.verbose:
        "Done."
    return filename


def process_image(image_file_name):
    """
    Apply computer vision techinques to the image.
    """
    # Here we're using a command-line utility to convert from
    # the satellite JPEG 2000 + wavelet format to PPM, something
    # which all OpenCV installations can process.
    # On a Linux system, installing libopenjp2-tools will satisfy
    # this dependency.
    system("opj_decompress -i {0}.jp2 -o {0}.ppm >> /dev/null".format(
        image_file_name))
    image_data = cv2.imread(image_file_name + '.ppm', 0)
    # Here we can use the SURF algorithm to pick out features.
    # Note that you'll need to have a version of OpenCV with the
    # contrib section installed; using the opencv-contrib-python
    # package satisfies this dependency.
    try:
        surf = cv2.xfeatures2d.SURF_create()
        (kps, descs) = surf.detectAndCompute(image_data, None)
        print("# kps: {0}, descriptors: {1}".format(len(kps), descs.shape))
        feature_image = cv2.drawKeypoints(image_data, kps,
                                          None, (255, 0, 0), 4)
        cv2.imshow(feature_image), cv2.show()
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    except Exception as err:
        print("Unable to use feature detection: {0}".format(err))
    return True


# Things to do when this module is directly run.
if __name__ == '__main__':
    image_file_name = choose_and_fetch_image()
    if image_file_name:
        is_interesting = process_image(image_file_name)
