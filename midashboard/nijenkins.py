from jenkinsapi.jenkins import Jenkins
import urllib3
import json
import logging


def get_nijenkins():
    jenkins_url = 'https://nijenkins'
    server = Jenkins(jenkins_url, username='testfarm', password='welcome', ssl_verify=False, lazy=True, timeout=300)
    return server


def get_all_jobs_in_view(jenkins, view_url):
    view = jenkins.get_view_by_url(view_url)
    jobs_dict = view.get_job_dict()
    return [jenkins.get_job_by_url(url, name) for name, url in jobs_dict.items()]


def safe_read_build_number(job, build_type):
    try:
        build_info = job._data[build_type]
        if build_info is not None:
            return build_info['number']
        else:
            return 0
    except KeyError:
        return 0


def scan_build_results_in_view(jenkins, view_url):
    results = []
    jobs = get_all_jobs_in_view(jenkins, view_url)

    for job in jobs:
        logging.debug(f'Checking job: {job}')
        # last_good_build_number = safe_read_build_number(job.get_last_good_buildnumber)
        last_good_build_number = safe_read_build_number(job, 'lastSuccessfulBuild')
        last_failed_build_number = safe_read_build_number(job, 'lastUnsuccessfulBuild')
        last_build_number = max(last_good_build_number, last_failed_build_number)
        result = {
            'name'      : job.name,
            'url'       : job.url,
            'build_num' : last_build_number,
            'passed'    : (last_good_build_number > last_failed_build_number)
        }
        results.append(result)
        logging.debug(f'Last Success #{last_good_build_number}, Last Failed #{last_failed_build_number}')

    return results


def get_build_result(view_url):

    nijenkins = get_nijenkins()

    logging.debug(f'Getting build result from [{view_url}]')
    build_results_details = scan_build_results_in_view(nijenkins, view_url)
    build_pass = all([build_result_details['passed'] for build_result_details in build_results_details])
    logging.debug(f'Build passed: {build_pass}')
    return {
        'build_pass': build_pass,
        'details': build_results_details
    }


if __name__ == '__main__':
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    # logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    # logging.getLogger("urllib3.connectionpool").disabled = True
    # logging.getLogger("urllib3.util.retry").disabled = True

    jenkins_view = "https://nijenkins/view/MI/view/PatternBasedDigital/view/Build/view/master/"
    build_result = get_build_result(jenkins_view)

    build_result_json = json.dumps(build_result, indent=4)
    print(build_result_json)
