  # bsky-bridge: A Python Library for the BlueSky API

  `bsky-bridge` is a Python library designed to bridge the interaction between Python applications and the BlueSky Social Network via its API.

  ## Table of Contents

  - [Features](#features)
  - [Installation](#installation)
  - [Usage](#usage)
    - [Creating a Session](#creating-a-session)
    - [Posting Content](#posting-content)
    - [Posting Images](#posting-images)
    - [Posting with Language Specification](#Posting-with-Language-Specification)
  - [Contribution](#contribution)
  - [License](#license)

  ## Features

  - Easy authentication with the BlueSky API.
  - Functions to post text and images to BlueSky via the API.
  - Parser to identify and extract mentions (@handle), links (URLs), and hashtags (#tags) from text, useful for processing and formatting posts.
  - Session persistence and automatic token refresh to handle authentication efficiently and prevent rate limiting.
  - Optional Language Specification: Users can manually specify the languages of their posts using the langs parameter to enhance filtering and parsing capabilities.

  ## Installation

  ```bash
  pip install bsky-bridge
  ```

  ## Usage

  ### Creating a Session

  Start by establishing a session with your BlueSky handle and **App passwords** *(To be created in your account settings)*:

  ```python
  from bsky_bridge import BskySession

  session = BskySession("your_handle.bsky.social", "your_APPpassword")
  ```

  ### Posting Content

  After initializing a session, you can post text to BlueSky:

  ```python
  from bsky_bridge import BskySession, post_text

  session = BskySession("your_handle.bsky.social", "your_APPpassword")

  response = post_text(session, "Hello BlueSky!")
  print(response)
  ```

  ### Posting Images

  To post images along with text, you can use the `post_image` method:

  ```python
  from bsky_bridge import BskySession, post_image

  session = BskySession("your_handle.bsky.social", "your_APPpassword")

  postText = "Check out this cool image!"
  imagePath = "path_to_your_image.jpeg"
  altText = "An awesome image"
  response = post_image(session, postText, imagePath, altText)
  print(response)
  ```

  **Note**: The library automatically handles resizing and compressing larger images to ensure they do not exceed 1 MB in size, all while maintaining a quality balance. This ensures efficient and quick image uploads.

  ### Posting with Language Specification
  To specify the languages of your post, simply add the langs parameter.

  ```python
  from bsky_bridge import BskySession, post_image

  # Initialize the session
  session = BskySession("your_handle.bsky.social", "your_APPpassword")

  # Define your post text and specify languages
  text = "Bonjour le monde!\nHello World!"
  specified_langs = ["fr", "en-US"]

  # Post the text with specified languages
  response = post_text(session, text, langs=specified_langs)
  print(response)


  # Define your post text, image path, alt text, and specify languages
  post_text_content = "Check out this beautiful sunset!\nมองดูพระอาทิตย์ตกที่สวยงามนี้!"
  image_path = "sunset.jpeg"
  alt_text = "Sunset over the mountains"
  specified_langs = ["en-US", "th"]

  # Post the image with specified languages
  response = post_image(
      session,
      post_text_content,
      image_path,
      alt_text,
      langs=specified_langs
  )
  print(response)
  ```

  ## Contribution

  Contributions are welcome! Please submit issues for any bug or problem you discover, and pull requests for new features or fixes.

  ## License

  [MIT License](LICENSE)
