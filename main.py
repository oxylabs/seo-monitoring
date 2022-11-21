import time
import config
import files
import tasks

from os.path import join


def input_file_watcher(poll_time: int):
    while True:
        print("<<<< ................. Sleeping")
        time.sleep(poll_time)  # the sleep loop
        print("Sleep ended .............. >>>>")

        print("Checking for new input files")
        input_files = files.check_for_new_input_files(config.INPUT_KEYWORDS)
        if len(input_files) == 0:
            print("No new input files found, continuing sleep")
            continue

        print("Found new input files, processing...")
        # f is a tuple of (directory_path, file_name)
        for f in input_files:
            print(f"Processing new file: {f[1]}")
            keywords_list = files.read_keywords_input_file(join(f[0], f[1]), f[1])

            print("Creating SERP Scraper API task")
            if keywords_list:
                scrape_task_results = tasks.create_serp_scraping_task_group(keywords_list)

                if scrape_task_results["results"]:
                    print("Creating new output file")
                    output = files.make_output_file(scrape_task_results["results"],
                                                    config.OUTPUT_FILE_TYPE,
                                                    config.OUTPUT_FILE_NAME,
                                                    config.OUTPUT_KEYWORDS, True)
                    if output:
                        print("Moving input file to processed directory")
                        files.move_processed_input_file(f[0], f[1], config.INPUT_PROCESSED)
                        print(f"Saved new output file {output['file_path']}")
                    else:
                        print("Unable to create OUTPUT file, leaving INPUT file for retry")


input_file_watcher(config.INPUT_POLL_TIME)
