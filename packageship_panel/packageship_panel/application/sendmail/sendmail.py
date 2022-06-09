# You may obtain a copy of Mulan PSL v2 at:
#!/usr/bin/python3
# ******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2022-2022. All rights reserved.
# licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# ******************************************************************************/
from builtins import len, range
import copy
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
import os
from requests.auth import HTTPBasicAuth
import socket
import time
import smtplib
from email.mime.text import MIMEText
import sched
from datetime import datetime
import csv
import builtins
from packageship_panel.application.query.panel import PanelInfo
from packageship_panel.application.core.obs import ObsInfo
from packageship_panel.libs.api.obs import ObsApi
from packageship_panel.application.core.tracking import ObsSynchronization
from packageship.libs.conf import configuration
from packageship.libs.log import LOGGER
from packageship.application.common.exc import (
    ElasticSearchQueryException,
    DatabaseConfigException,
)


class Mail:
    """
    Query the database and automatically send a reminder email
    """

    mail_sched = sched.scheduler(time.time, time.sleep)
    count = 2  # query times
    file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                             "mail_content.html")
    unstable_items = []
    cc_receiver = []
    repo_keys = {
        "en": [
            "repo_name", "gitee_version", "obs_branch", "architecture",
            "build_status", "build_detail_link", "build_time", "name",
            "maintainer", "contributors"
        ],
        "cn": [
            "repo仓名", "gitee版本", "obs分支", "架构", "编译状态", "详情链接", "编译耗时", "sig组",
            "maintainer", "contributors"
        ]
    }

    def __init__(
        self,
        port=465,
    ):
        self.sender, self.password, self.mailhost = (
            os.getenv("EMAIL_SENDER"),
            os.getenv("EMAIL_PASSWORD"),
            os.getenv("MAIL_HOST"),
        )
        if not all([self.sender, self.password, self.mailhost]):
            raise RuntimeError("please set environment first")
        self.port = port
        self.mail_sended = list()
        # Store the branch name of the mail that has been sent
        self.mail_unstable = dict()
        # Store the branch name that is unstable
        self.gitee_obs_dict = dict()
        self.obstate = ""
        self.obs_api_dict = list()
        # Store the branch name that is publish and need to be query
        self._pi = PanelInfo()
        self.obs_sync = ObsSynchronization()
        self.obs = ObsInfo()

    def repo_find_blank(self, res_repo_items, receiver, bcc_receiver):
        """
        Replace "" for nonexistent or equal to None
        param: data from es
        """
        repo_keys = self.repo_keys["en"]
        res_repo_dict = {}
        for repo_items in repo_keys:
            res_repo_dict[repo_items] = res_repo_items.get(repo_items, "")

        self.repo_id_info(res_repo_dict, receiver, bcc_receiver)
        return res_repo_dict

    @staticmethod
    def _get_maintainers(res_repo_dict, key, email_receivers):
        '''
        Obtain maintainier mailbox information, including string data output to emails and CSV files
        '''
        maintainers_ids = ""
        csv_maintainers = ""
        m_count = 0  # set the totall count of maintainer/contributors
        for res_maintainer in res_repo_dict.get(key, []):
            if res_maintainer.get("id") and m_count < 3:
                m_count += 1
                maintainers_ids = (
                    f"{maintainers_ids}<b>id:</b>{str(res_maintainer['id'])}    <b>email:</b>{str(res_maintainer['email'])}<br>"
                )
            if res_maintainer.get("id"):
                csv_maintainers = f"{csv_maintainers}id:{str(res_maintainer['id'])}    email:{str(res_maintainer['email'])}\n"
            if res_maintainer.get("email"):
                email_receivers.append(res_maintainer["email"])
        return maintainers_ids, csv_maintainers

    def repo_id_info(self, res_repo_dict, receiver, bcc_receiver):
        """
        Concatenate HTML script and data into the content of the email
        param:dictionary format,contains all the information needed for the email
        """
        (res_repo_dict["maintainer"],
         res_repo_dict["csv_maintainer"]) = self._get_maintainers(
             res_repo_dict, "maintainer", receiver)
        (res_repo_dict["contributors"],
         res_repo_dict["csv_contributors"]) = self._get_maintainers(
             res_repo_dict, "contributors", bcc_receiver)

    def _load_tmp_file(self):
        '''
        Gets the HTML file content
        '''
        try:
            with open(self.file_path, "r", encoding="utf-8") as mf:
                template_content = mf.read()
        except (IOError, ValueError) as error:
            LOGGER.error(error)
            return None

        else:
            return template_content

    def _get_attachment(self, gitee_branch, csv_dict):
        '''
        Write details to the attachment
        '''
        header = self.repo_keys["cn"]
        date_today = datetime.today().date()
        file_path_csv = f'{configuration.TEMPORARY_DIRECTORY}/{str(date_today)}-{gitee_branch}.csv'
        with os.fdopen(os.open(file_path_csv,
                               os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o640),
                       'w',
                       encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for i in range(0, len(csv_dict)):
                csv_dict[i].pop("maintainer", None)
                csv_dict[i].pop("contributors", None)
                csv_list = [val for _, val in csv_dict[i].items()]
                writer.writerow(csv_list)
        return f'{date_today}-{gitee_branch}.csv'

    def _get_repo_table(self, res_repo):
        '''
        get detail information in repo_table
        '''

        def table_td(val, key, td, res_repo_dict):
            if key in ["build_status", "csv_maintainer", "csv_contributors"]:
                return td
            if key == "build_detail_link":
                td += f'<td><a href="{val}">{res_repo_dict["build_status"]}</a></td> '
            else:
                td += f"<td border=\"1px\" bordercolor=\"#ddd\">{str(val)}</td>"
            return td

        table_tr = ""
        receiver, bcc_receiver = list(), list()
        # find the blank items in res_repo
        csv_dict = []
        for res_repo_item in res_repo:
            tds = ""
            # get email address from res_repo_dict in repo_find_blank
            res_repo_dict = self.repo_find_blank(res_repo_item, receiver,
                                                 bcc_receiver)
            csv_dict.append(res_repo_dict)
            for key, value in res_repo_dict.items():
                tds = table_td(value, key, tds, res_repo_dict)

            table_tr = table_tr + "<tr>" + tds + "</tr>"
        receiver = list(set(receiver))
        bcc_receiver = list(set(bcc_receiver))

        return table_tr, csv_dict, receiver, bcc_receiver

    def get_sig_package_state(self, gitee_branch):
        '''
        Get sig group statistics and make sort
        '''
        res_sig_temp = dict()
        res_sig_list = list()
        res_sig = self._pi.query_sig_package_state(branch=gitee_branch)
        for key, dicts in res_sig.items():
            res_sig_temp = dict()
            res_sig_temp["name"] = key
            res_sig_temp["result"] = dict()
            failed_sum = 0
            unresolved_sum = 0
            for key, value in dicts.items():
                if ("failed" in value):
                    failed_sum += value["failed"]
                if ("unresolved" in value):
                    unresolved_sum += value["unresolved"]
            res_sig_temp["result"]["failed"] = failed_sum
            res_sig_temp["result"]["unresolved"] = unresolved_sum
            res_sig_temp["result"]["sum"] = failed_sum + unresolved_sum
            res_sig_list.append(res_sig_temp)
        for i in range(1, len(res_sig_list)):
            for j in range(0, len(res_sig_list) - i):
                if (res_sig_list[j]["result"]["sum"] <
                        res_sig_list[j + 1]["result"]["sum"]):
                    res_sig_list[j], res_sig_list[j + 1] = res_sig_list[
                        j + 1], res_sig_list[j]
        return res_sig_list

    def _get_sig_table(self, gitee_branch):
        '''
        Collect sig group information and add it to td table
        '''

        def sig_table_td(val, tds, add_color):
            tds = tds + \
                f"<td border=\"1px\" bordercolor=\"#ddd\">{add_color[0]}{str(val)}{add_color[1]}</td>"
            return tds

        sig_table_tr = ""
        tds = ""
        res_sig_list = self.get_sig_package_state(gitee_branch=gitee_branch)
        i = 0
        add_color = ["", ""]
        for items in res_sig_list:
            add_color = ["", ""]
            if i < 3:
                add_color = ["<font color=\"#FF0000\">", "</font>"]
            tds = ""
            tds = sig_table_td(items["name"], tds, add_color)
            tds = sig_table_td(items["result"]['failed'], tds, add_color)
            tds = sig_table_td(items["result"]['unresolved'], tds, add_color)
            sig_table_tr = sig_table_tr + "<tr>" + tds + "</tr>"
            i += 1

        return sig_table_tr

    def _mail_content(self, gitee_branch, res_status, res_times,
                      obs_success_rate, table_tr, sig_table_tr, csv_dict):
        """
        fill subject and content in mail
        """
        merge_res = (dict(res_status,
                          **res_times,
                          obs_branch=gitee_branch,
                          obs_success_rate=obs_success_rate,
                          content_tr_repo=table_tr,
                          content_tr_sig=sig_table_tr))
        time_now = str(datetime.now().astimezone().strftime("%Y-%m-%d"))
        subject = "{time_now} gitee分支【{branch}】 问题单缺陷统计报告，请及时注意问题及时解决！".format(
            time_now=time_now, branch=gitee_branch)

        template_content = self._load_tmp_file()
        if not template_content:
            raise ValueError("template content is empty.")
        content = template_content.format(**merge_res).replace("^",
                                                               "{").replace(
                                                                   "$", "}")

        # attachment
        csv_file_name = self._get_attachment(gitee_branch=gitee_branch,
                                             csv_dict=csv_dict)
        csv_file_path = os.path.join(configuration.TEMPORARY_DIRECTORY,
                                     csv_file_name)
        csvfile = MIMEApplication(open(csv_file_path, 'rb').read())
        csvfile.add_header('Content-Disposition',
                           'attachment',
                           filename=csv_file_name)
        # reciver list

        return content, subject, csvfile

    def _send_email(self, content, subject, receiver, bcc_receiver, csvfile):
        '''
        send mail from xxx@gitee.com
        param:
        receiver, bcc_receiver:receiver list
        csvfil:attachment file
        subject:title
        content:mail content,html script
        '''
        mime_mail = MIMEMultipart()
        mime_mail.attach(MIMEText(content, _subtype="html", _charset="utf-8"))
        mime_mail.attach(csvfile)
        mime_mail["Subject"] = subject
        mime_mail["form"] = self.sender
        mime_mail["to"] = ",".join(bcc_receiver)
        mime_mail["cc"] = ",".join(receiver)

        # create link
        try:
            smtp = smtplib.SMTP_SSL(self.mailhost, self.port)
            smtp.login(self.sender, self.password)
            smtp.sendmail(self.sender, receiver +
                          bcc_receiver, mime_mail.as_string())
            LOGGER.info("mail send success!")
            return True
        except (smtplib.SMTPException, socket.gaierror) as error:
            LOGGER.error(f"Failed to send email,excetion info {str(error)}")
            return False
        finally:
            smtp.quit()

    def _get_gitee_map_obs_form_api(self):
        '''
        Use API interface to obtain real-time OBS project status
        '''
        self.gitee_obs_dict = self._pi.query_suggest_info(index="branch_info",
                                                          body={})
        # gitee_obs_dict=copy.deepcopy(self.gitee_obs_dict)
        gitee_obs_dict = list()
        for items in self.gitee_obs_dict:
            obs_branchs = items["obs_branch"]
            obsapi = ObsApi()
            body = {"gitee_branch": items["gitee_branch"], "obs_branch": []}
            for obs_branch in obs_branchs:
                obsapi.get_project_state(obs_branch["name"])
            for obs_states in obsapi.obs_states:
                body["obs_branch"].append({
                    "name": obs_states[0],
                    "state": obs_states[1]
                })
            gitee_obs_dict.append(body)
        self.obs_api_dict = gitee_obs_dict

    def _query_fail_branch(self, unstable_branch):
        """
        Check whether the unstable branch of the current query failed
        param unstable_branch:branch name
        """
        res = self._pi.query_suggest_info(
            index="branch_info", body={"gitee_branch": unstable_branch})
        for re in res:
            for re_status in re["obs_branch"]:
                if (re_status["state"] != "published"):
                    return True
        return False

    def _query_branch(self):
        """
        The first query sends information about the branch that has stabilized and failed
        """
        if not self.gitee_obs_dict:
            return
        for item in self.gitee_obs_dict:
            self.mail_unstable[item["gitee_branch"]] = []
            for item_state in item["obs_branch"]:
                self.mail_unstable[item["gitee_branch"]].append(
                    item_state["name"])

    def _get_info(self, query_item):
        """
        For branch that is stable after a query: send mail directly
        param query_item:obs_branch name
        """
        query_dict = {"gitee_branch": query_item, "build_status": "failed"}
        faileds = self._pi.query_obs_info(query_dict)
        query_dict["build_status"] = "unresolvable"
        unresolvables = self._pi.query_obs_info(query_dict)

        return faileds + unresolvables

    def _send_remove_unstable(self, gitee_items):
        '''
        send email and remove this item from self.mail_unstable
        '''
        send_obs_branch = self.send_obs_info(gitee_items)
        if not send_obs_branch:
            return
        for item in send_obs_branch:
            if item in self.mail_unstable[gitee_items]:
                self.mail_unstable[gitee_items].remove(item)

    def _sched_query_unstable(self):
        """
        In the mail_unstable array, search for the branch where
        the current build failed and send mail
        """
        for gitee_items in self.mail_unstable:
            if (gitee_items in self.mail_sended
                    or self.mail_unstable[gitee_items] == []):
                continue
            self._get_gitee_map_obs_form_api()
            for items in self.obs_api_dict:
                for obs_branch in items["obs_branch"]:
                    if (obs_branch["state"] != "published"):
                        self.obs_api_dict.remove(items)
                        break
            for items in self.obs_api_dict:
                if items["gitee_branch"] not in self.mail_sended:
                    self._send_remove_unstable(items["gitee_branch"])

    def _sched_start(self, inc):
        """
        A timed task entry function that waits until all branches have sent an email
        or until the loop ends count times
        param inc:wait time
        """
        LOGGER.info("enter sched function in" +
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        if (self.count > 0 and any(
            [True if va else False for _, va in self.mail_unstable.items()])
                and len(self.mail_sended) < len(self.obs_api_dict)):
            self.count -= 1
            self._sched_query_unstable()
            self.mail_sched.enter(inc, 0, self._sched_start, (inc, ))

    def _get_mail_times_or_status(self, gitee_name, branch_architecture_items,
                                  mail, query_func):
        '''
        Get obs project build time or status statistics from the database
        '''
        mail_temp = query_func(branch=gitee_name,
                               architecture=branch_architecture_items)
        for key, value in mail_temp.items():
            if key in mail:
                mail[key] += value
            else:
                mail[key] = value

    def send_obs_info(self, gitee_branch):
        """
        given obs branch name,send email
        param:gitee branch name,exp:master
        """
        mail_content = self._get_info(gitee_branch)
        if not mail_content:
            return
        # mark the obs branch that will be sended
        send_obs_branch = set([
            mail_content_item["obs_branch"]
            for mail_content_item in mail_content
        ])
        for send_items in copy.deepcopy(send_obs_branch):
            if send_items not in self.mail_unstable[gitee_branch]:
                send_obs_branch.remove(send_items)
                     
        if not send_obs_branch:
            return None
        
        branch_architecture = set([
            mail_content_item["architecture"]
            for mail_content_item in mail_content
        ])

        mail_status, mail_times = dict(), dict()

        for branch_architecture_items in branch_architecture:
            self._get_mail_times_or_status(
                gitee_branch,
                branch_architecture_items,
                mail_status,
                self._pi.query_build_states,
            )
            self._get_mail_times_or_status(
                gitee_branch,
                branch_architecture_items,
                mail_times,
                self._pi.query_build_times,
            )
        iso_info_thirty = len(self._pi.query_iso_info(branch=gitee_branch))
        iso_success_rate = "{:.2f}%".format(iso_info_thirty / 30 * 100)

        table_tr, csv_dict, receiver, bcc_receiver = self._get_repo_table(
            res_repo=mail_content)
        sig_table_tr = self._get_sig_table(gitee_branch=gitee_branch)
        try:
            (content, subject,
             csvfile) = self._mail_content(gitee_branch, mail_status,
                                           mail_times, iso_success_rate,
                                           table_tr, sig_table_tr, csv_dict)
        except ValueError:
            return

        ret = self._send_email(content, subject, receiver, bcc_receiver,
                               csvfile)
        # get the real length from self.gitee_obs_dict[gitee_branch]
        length = 0
        for gitee_obs_dict_items in self.gitee_obs_dict:
            if (gitee_obs_dict_items["gitee_branch"] == gitee_branch):
                length = len(gitee_obs_dict_items["obs_branch"])
                break
        if ret and len(send_obs_branch) == length:
            self.mail_sended.append(gitee_branch)

        for item in send_obs_branch:
            if item in self.mail_unstable[gitee_branch]:
                self.mail_unstable[gitee_branch].remove(item)
                
        # delete the file
        file_name = f'{configuration.TEMPORARY_DIRECTORY}/{str(datetime.today().date())}-{gitee_branch}.csv'
        if (os.path.isfile(file_name)):
            os.remove(file_name)
        else:
            LOGGER.error("delete file{filename} failed,please check".format(
                filename=file_name))

        # Enter the schedStart scheduling task function

        return send_obs_branch

    async def start(self):
        """
        The entry function queries the existing stable and failed OBS branches,
        and then circulates the unstable branches
        """
        try:
            self._get_gitee_map_obs_form_api()
            self._query_branch()
            for query_item in self.mail_unstable:
                self.send_obs_info(query_item)

            stime = 10  # call _sched_start every 60 seconds
            self.mail_sched.enter(0, 0, self._sched_start, (stime, ))
            self.mail_sched.run()
        except (ElasticSearchQueryException, DatabaseConfigException) as error:
            LOGGER.error(f"database exception{error}")
