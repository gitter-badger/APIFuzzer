#!/usr/bin/env python2.7
from __future__ import print_function
import sys
import argparse
import json

if sys.version_info[:2] == (2, 7):
    from kitty.interfaces import WebInterface
    from kitty.model import GraphModel

    from apifuzzer.swagger_template_generator import SwaggerTemplateGenerator
    from apifuzzer.fuzzer_target import FuzzerTarget
    from apifuzzer.server_fuzzer import OpenApiServerFuzzer


class Fuzzer(object):
    def __init__(self, api_resources, report_dir, test_level, alternate_url=None, test_result_dst=None):
        self.api_resources = api_resources
        self.base_url = alternate_url
        self.templates = None
        self.test_level = test_level
        self.report_dir = report_dir
        self.test_result_dst = test_result_dst

    def prepare(self):
        # here we will be able to branch the template generator if we would like to support other than Swagger
        template_generator = SwaggerTemplateGenerator(self.api_resources)
        template_generator.process_api_resources()
        self.templates = template_generator.templates
        if not self.base_url:
            self.base_url = template_generator.compile_base_url()

    def run(self):
        target = FuzzerTarget(name='target', base_url=self.base_url, report_dir=self.report_dir)
        interface = WebInterface()
        model = GraphModel()
        for template in self.templates:
            model.connect(template.compile_template())
        fuzzer = OpenApiServerFuzzer()
        fuzzer.set_model(model)
        fuzzer.set_target(target)
        fuzzer.set_interface(interface)
        fuzzer.start()


if __name__ == '__main__':
    if not sys.version_info[:2] == (2, 7):
        print('Please use with Python 2.7')
        exit()

    parser = argparse.ArgumentParser(description='API fuzzer configuration',
                                     formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=20))
    parser.add_argument('-s', '--src_file',
                        type=str,
                        required=True,
                        help='API definition file path',
                        dest='src_file')
    parser.add_argument('-r', '--report_dir',
                        type=str,
                        required=False,
                        help='Directory where error reports will be saved, default: /tmp/',
                        dest='report_dir',
                        default='/tmp/')
    parser.add_argument('-l', '--level',
                        type=int,
                        required=False,
                        help='Test deepness: [1,2], higher is the deeper !!!Not implemented!!!',
                        dest='level',
                        default=1)
    parser.add_argument('-u', '--url',
                        type=str,
                        required=False,
                        help='Use CLI defined url instead compile the url from the API definition. Useful for testing',
                        dest='alternate_url',
                        default=None)
    parser.add_argument('-t', '--test_report',
                        type=str,
                        required=False,
                        help='JUnit test result xml save path !!!Not implemented!!!',
                        dest='test_result_dst',
                        default=None)
    args = parser.parse_args()
    api_definition_json = dict()
    try:
        with open(args.src_file, 'r') as f:
            api_definition_json = json.loads(f.read())
    except Exception as e:
        print('Failed to parse input file: {}'.format(e))
        exit()
    prog = Fuzzer(api_resources=api_definition_json,
                  report_dir=args.report_dir,
                  test_level=args.level,
                  alternate_url=args.alternate_url,
                  test_result_dst=args.test_result_dst
                  )
    prog.prepare()
    prog.run()
