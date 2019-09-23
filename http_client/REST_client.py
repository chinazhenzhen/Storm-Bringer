"""
http base class RESTClientObject
基于rest的三方api封装：RESTClientObject
可以通过此http类去请求基于RESTful设计的api
"""
import re
import json

import urllib3
import certifi
from six.moves.urllib.parse import urlencode


class RESTClientObject:

    def __init__(self, pools_size=4, configuration=None):
        """
        :param pools_size: urllib3 config
        :param configuration: we need configuration in the future
        """
        self.pool_manager = urllib3.PoolManager(
            num_pools=pools_size,
            cert_reqs='CERT_REQUIRED',
            ca_certs=certifi.where()
        )

    def request(self, method, url, query_params=None, headers=None, body=None, post_params=None):
        """
        :param method: http request method
        :param url: http request url
        :param query_params: query parameters in the url
        :param headers: http request headers
        :param body: request json body, for `application/json`
        :param post_params: request post parameters,
                            `application/x-www-form-urlencoded`
                            and `multipart/form-data`
        :return:
        """
        method = method.upper()
        assert method in ['GET', 'HEAD', 'DELETE', 'POST', 'PUT', 'PATCH', 'OPTIONS']

        if post_params and body:
            raise ValueError("body parameter cannot be used with post_params parameter.")
        post_params = post_params or {}
        headers = headers or {}
        if 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'

        try:
            # For `POST`, `PUT`, `PATCH`, `OPTIONS`, `DELETE`
            if method in ['POST', 'PUT', 'PATCH', 'OPTIONS', 'DELETE']:
                if query_params:
                    url += '?' + urlencode(query_params)

                if re.search('json', headers['Content-Type'], re.IGNORECASE):
                    if headers['Content-Type'] == 'application/json-patch+json':
                        if not isinstance(body, list):
                            headers['Content-Type'] = 'application/strategic-merge-patch+json'
                    request_body = None
                    if body is not None:
                        request_body = json.dumps(body)
                    r = self.pool_manager.request(method=method,
                                                  url=url,
                                                  body=request_body,
                                                  headers=headers,
                                                  )

                elif headers['Content-Type'] == 'application/x-www-form-urlencoded':
                    r = self.pool_manager.request(method=method,
                                                  url=url,
                                                  fields=post_params,
                                                  encode_multipart=False,
                                                  headers=headers
                                                  )

                elif headers['Content-Type'] == 'multipart/form-data':
                    # must del headers['Content-Type'], or the correct Content-Type. which generated by urllib3 will be overwritten.
                    del headers['Content-Type']
                    r = self.pool_manager.request(method=method,
                                                  url=url,
                                                  fields=post_params,
                                                  encode_multipart=True,
                                                  headers=headers)

                elif isinstance(body, str):
                    request_body = body
                    r = self.pool_manager.request(method=method,
                                                  url=url,
                                                  body=request_body,
                                                  headers=headers
                                                  )

                else:
                    msg = """Cannot prepare a request message for provided arguments.
                                 Please check that your arguments match declared content type."""
                    raise ApiException(status=0, reason=msg)

            # For `GET`, `HEAD`
            else:
                r = self.pool_manager.request(method=method,
                                              url=url,
                                              fields=query_params,
                                              headers=headers
                                              )

        except Exception as error:
            msg = "{0}\n{1}".format(type(error).__name__, str(error))
            raise ApiException(status=0, reason=msg)

        if not 200 <= r.status <= 299:
            raise ApiException(http_resp=r)

        return r

    def GET(self, url, headers=None, query_params=None):
        return self.request("GET", url,
                            headers=headers,
                            query_params=query_params)

    def HEAD(self, url, headers=None, query_params=None):
        return self.request("HEAD", url,
                            headers=headers,
                            query_params=query_params)

    def OPTIONS(self, url, headers=None, query_params=None, post_params=None, body=None):
        return self.request("OPTIONS", url,
                            headers=headers,
                            query_params=query_params,
                            post_params=post_params,
                            body=body)

    def DELETE(self, url, headers=None, query_params=None, body=None):
        return self.request("DELETE", url,
                            headers=headers,
                            query_params=query_params,
                            body=body)

    def POST(self, url, headers=None, query_params=None, post_params=None, body=None):
        return self.request("POST", url,
                            headers=headers,
                            query_params=query_params,
                            post_params=post_params,
                            body=body)

    def PUT(self, url, headers=None, query_params=None, post_params=None, body=None):
        return self.request("PUT", url,
                            headers=headers,
                            query_params=query_params,
                            post_params=post_params,
                            body=body)

    def PATCH(self, url, headers=None, query_params=None, post_params=None, body=None):
        return self.request("PATCH", url,
                            headers=headers,
                            query_params=query_params,
                            post_params=post_params,
                            body=body)


class ApiException(Exception):

    def __init__(self, status=None, reason=None, http_resp=None):
        if http_resp:
            self.status = http_resp.status
            self.reason = http_resp.reason
            self.body = http_resp.data
            self.headers = http_resp.getheaders()
        else:
            self.status = status
            self.reason = reason
            self.body = None
            self.headers = None

    def __str__(self):
        """
        Custom error messages for exception
        """
        error_message = "({0})\n"\
                        "Reason: {1}\n".format(self.status, self.reason)
        if self.headers:
            error_message += "HTTP response headers: {0}\n".format(self.headers)

        if self.body:
            error_message += "HTTP response body: {0}\n".format(self.body)

        return error_message