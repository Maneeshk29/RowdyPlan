"""Static media responses with byte-range support for video seeking."""

from baize.asgi import FileResponse as RangeFileResponse
from starlette.datastructures import Headers
from starlette.staticfiles import NotModifiedResponse, StaticFiles


class MediaStaticFiles(StaticFiles):
    def file_response(self, full_path, stat_result, scope, status_code=200):
        # Retain Starlette's path validation and conditional caching; Baize handles ranges.
        response = RangeFileResponse(str(full_path), stat_result=stat_result)
        if self.is_not_modified(response.headers, Headers(scope=scope)):
            return NotModifiedResponse(response.headers)
        return response
