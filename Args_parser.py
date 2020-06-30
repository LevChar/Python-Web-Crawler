import argparse
import json

def args_parser():
	parser = argparse.ArgumentParser(description='Site Crawler [Python]')
	parser.add_argument('-n', '--num_workers', type=int, default=5000,
						help="Maximal number of worker threads. Default is: [5,000]")
	parser.add_argument('-q', '--max_queue_size', type=int, default=10000,
						help="Maximal size of working queue. Default is: [10,000]")
	parser.add_argument('-o','--output', action="store", default=None,
						help="Output file name. Default is: ['output.txt']")
	parser.add_argument('-l', '--log', type=int, default=1,
						help="Log level [0-basic, 1-standard[default], 2-verbose]")

	group = parser.add_mutually_exclusive_group()
	group.add_argument('-c', '--config', action="store", default=None,
					   help="Configuration file in json format")
	group.add_argument('-d', '--domain', action="store", default="",
					   help="Target domain like: [https://www.guardicore.com]")

	args = parser.parse_args()

	# Read config file if it was provided
	if args.config is not None:
		try:
			config_data=open(args.config,'r')
			config = json.load(config_data)
			config_data.close()
		except Exception as e:
			print(f"Config file: ['{args.config}'] couldn't be opened, please check the file exists.")
			config = {}
	else:
		config = {}

	# Adjust configuration be users given flag parameters
	dict_arg = args.__dict__
	for arg in config:
		if arg in dict_arg:
			dict_arg[arg] = config[arg]
	del(dict_arg['config'])

	if dict_arg["domain"] == "":
		print ("Error: Domain wasn't provided. Exiting...")
		exit()

	return dict_arg