def convert_pixels_distance_to_meters(pixels_distance, reference_height_in_pixels, reference_height_in_meters):
    return (pixels_distance * reference_height_in_meters) / reference_height_in_pixels

def convert_meters_to_pixel_distance(meters, reference_height_in_meters, reference_height_in_pixels):
    return (meters * reference_height_in_pixels) / reference_height_in_meters