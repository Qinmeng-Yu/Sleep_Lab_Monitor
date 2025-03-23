import base64
# import io
# from matplotlib import pyplot as plt
# import matplotlib.image as mpimg


def read_file_as_b64(image_path):
    with open(image_path, "rb") as image_file:
        b64_bytes = base64.b64encode(image_file.read())
    b64_string = str(b64_bytes, encoding='utf-8')
    return b64_string


# def view_b64_image(base64_string):
#     image_bytes = base64.b64decode(base64_string)
#     image_buf = io.BytesIO(image_bytes)
#     i = mpimg.imread(image_buf, format='JPG')
#     plt.imshow(i, interpolation='nearest')
#     plt.show()
#     return


# def save_b64_image(base64_string):
#     image_bytes = base64.b64decode(base64_string)
#     with open("new-img.jpg", "wb") as out_file:
#         out_file.write(image_bytes)
#     return


if __name__ == '__main__':
    img_b64_string = read_file_as_b64("flow_plot.jpg")
    print(img_b64_string)
    # save_b64_image(b64_string)
