#  Copyright 2024 Palantir Technologies, Inc.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.


from compute_modules.logging import internal

DEBUG_STR = "I'm a little teapot"
INFO_STR = "Short and stout"
WARNING_STR = "Here is my handle, here is my spout"
ERROR_STR = "When I get all steamed up hear me shout:"
CRITICAL_STR = "Tip me over and pour me out!"

CLIENT_DEBUG_STR = "twinkle twinkle little star"
CLIENT_INFO_STR = "how I wonder what you are"
CLIENT_WARNING_STR = "up above the world so high"
CLIENT_ERROR_STR = "like a diamond in the sky"
CLIENT_CRITICAL_STR = "oh nvm that's a planet"


def _emit_internal_logs() -> None:
    logger = internal.get_internal_logger()
    logger.debug(DEBUG_STR)
    logger.info(INFO_STR)
    logger.warning(WARNING_STR)
    logger.error(ERROR_STR)
    logger.critical(CRITICAL_STR)
