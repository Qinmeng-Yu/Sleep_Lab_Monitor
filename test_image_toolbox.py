
def test_read_file_as_b64():
    from image_toolbox import read_file_as_b64
    b64str = read_file_as_b64("test_image.jpg")
    assert b64str[0:20] == "/9j/4AAQSkZJRgABAQEA"
