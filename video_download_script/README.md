# Video downloading script.
AVA dataset contains some videos which are unreachable now. For reachable videos, this script uses `pafy`. For those unreachable videos, this script tries to download them from [this link](http://thoth.inrialpes.fr/ava/getava.php).

## Prerequisites
`pafy` and `youtube-dl`

## Usage
For reachable videos, just set the `--download_train` and `--download_test` flags as `True` and provide training and testing video ids files through `--train_file` and `--test_file`.

For unreachable videos, you need to go to [the link](http://thoth.inrialpes.fr/ava/getava.php) to request data for academic research by accepting its terms and conditions. Then you will get the user name and password. By setting the flags `--download_unavailable`, `--user_name` and `--password`, you are able to download the unreachable videos.
