################################################################################
# LexaLink Copyright information - do not remove this copyright notice
# Copyright (C) 2012 
#
# Lexalink - a free social network and dating website platform for the Google App Engine. 
#
# Original author: Alexander Marquardt
# Documentation and additional information: http://www.LexaLink.com
# Git source code repository: https://github.com/lexalink/LexaLink.git 
#
# Please consider contributing your enhancements and modifications to the LexaLink community, 
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################


import cgi 
import logging, traceback

from google.appengine.ext import blobstore
from google.appengine.api import images
from google.appengine.api import urlfetch


from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseRedirect


from models import PhotoModel, WatermarkPhotoModel
from constants import MAX_NUM_PHOTOS, SMALL_IMAGE_X, SMALL_IMAGE_Y, MEDIUM_IMAGE_X, MEDIUM_IMAGE_Y, LARGE_IMAGE_X, LARGE_IMAGE_Y
from utils import passhash, put_userobject
import error_reporting, utils_top_level
import settings, utils, constants

# The following should never be enabled - except to get the watermark images into the datastore. 
# This is a total hack. 
WRITE_WATERMARK_HACK = False

if WRITE_WATERMARK_HACK:
    logging.error("Warning: WRITE_WATERMARK_HACK is enabled")

# default size for watermark - Note, this value is only used when WRITE_WATERMARK_HACK is True - we only
# re-size the watermark when it is uploaded (not when it is being applied) for efficiency 
watermark_x = int(LARGE_IMAGE_X/1.5)
watermark_y = int(LARGE_IMAGE_Y/1.5)
main_watermark_opacity = 0.4
secondary_watermark_opacity = 0.4

if settings.BUILD_NAME == "Discrete":
    watermark_x = int(LARGE_IMAGE_X/1.1)
    watermark_y = int(LARGE_IMAGE_Y/1.1)
    main_watermark_opacity = 0.25
    secondary_watermark_opacity = 0.25

if settings.BUILD_NAME == "Language" or settings.BATCH_BUILD_NAME == "Friend":
    watermark_x = int(LARGE_IMAGE_X/1.1)
    watermark_y = int(LARGE_IMAGE_Y/1.1)
    
if settings.BUILD_NAME == "Gay":
    watermark_x = int(LARGE_IMAGE_X/1.5)
    watermark_y = int(LARGE_IMAGE_Y/1.5)

    
if settings.BUILD_NAME == "Swinger":
    watermark_x = int(LARGE_IMAGE_X/1.5)
    watermark_y = int(LARGE_IMAGE_Y/1.5)

def write_watermark_to_dabase(userobject, blob_info):
    
    # If an there is an existing watermark image, overwrite it - otherwise there is no reason 
    # that we are uploading a new image.
    
    if userobject.username == constants.ADMIN_USERNAME:
        watermark = WatermarkPhotoModel.all().get()
        if not watermark:
            # create a new one
            watermark = WatermarkPhotoModel()
        
        img = images.Image(blob_key=str(blob_info.key()))
        img.resize(watermark_x, watermark_y)
        watermark.image = img.execute_transforms(output_encoding=images.PNG)      
        watermark.put()
        
        error_reporting.log_exception(logging.warning, error_message = 'Writing new watermark to database')
        return HttpResponseRedirect('/rs/ajax/load_photos_for_edit/')
    else:
        # Only the user ADMIN should ever be allowed to upload a new watermark
        error_reporting.log_exception(logging.critical, error_message = 'Error user: %s has attempted to write a watermark to database' % userobject.username)
        return resize_and_put_photos(userobject, blob_info)

#############################################
def resize_and_put_photos(userobject, blob_info):
    # responsible for resizing and writing photo into database.
    # both request and userobject are passed in, because depending on from where the request 
    # is received, it could require extra processing to extract userobject (easier to pass in)

    num_photos = PhotoModel.query().filter(PhotoModel.parent_object == userobject.key).count(MAX_NUM_PHOTOS)
     
    # Check if user has used up their quota for photos. If so, we
    # silently fail (for now) -- TODO - add more informative error
    # message if user tries to exceed photo quota.
    if num_photos < MAX_NUM_PHOTOS:
       
        try:
            photo = PhotoModel()
            photo.name = blob_info.filename
            
            orig_img = images.Image(blob_key=str(blob_info.key()))  
            orig_img.resize(LARGE_IMAGE_X, LARGE_IMAGE_Y)
            uploaded_photo = orig_img.execute_transforms(output_encoding=images.PNG)
            photo.large_before_watermark = uploaded_photo

            watermark = WatermarkPhotoModel.query().get()
            if watermark and watermark.image:
                # make the composite image the same size as the original "resized" image
                composite_width = orig_img.width
                composite_height = orig_img.height
                    
                if composite_width >= composite_height:
                    # this is a landscape image (width greater than height)
                    composite_image = images.composite([(uploaded_photo , 0, 0, 1.0, images.TOP_CENTER), 
                                                        (watermark.image, 0,0, main_watermark_opacity, images.BOTTOM_CENTER)],
                                                       composite_width, composite_height)                    
                    
                    if composite_width < 2 * composite_height:
                        # if the image is very short and wide, then only place one horizontal watermark
                        composite_image = images.composite([(composite_image, 0, 0, 1.0, images.TOP_CENTER), 
                                                            (watermark.image, 0,0, secondary_watermark_opacity, images.TOP_CENTER)],
                                                           composite_width, composite_height)
                        

                else:
                    # image is taller than it is wide (is "portrait") - rotate the watermark to place on left and right sides of the photo
                    watermark_img = images.Image(watermark.image)
                    watermark_img.rotate(270)
                    rotated_watermark_image = watermark_img.execute_transforms(output_encoding=images.PNG)
                    composite_image = images.composite([(uploaded_photo, 0, 0, 1.0, images.TOP_CENTER), 
                                                        (rotated_watermark_image, 0,0, main_watermark_opacity, images.CENTER_LEFT)],
                                                       composite_width, composite_height)
                    
                    if composite_height < 2*composite_width:
                        watermark_img.rotate(180)
                        rotated_watermark_image = watermark_img.execute_transforms(output_encoding=images.PNG)
                        # if image is tall and skinny this secondary watermark will not be placed
                        composite_image = images.composite([(composite_image, 0, 0, 1.0, images.TOP_CENTER), 
                                                            (rotated_watermark_image, 0,0, secondary_watermark_opacity, images.CENTER_RIGHT)],
                                                           composite_width, composite_height)
                        

            else:
                # in reality this branch should never be hit - generate a warning
                if not settings.DEBUG:
                    # should never occur on the production server - while debugging it can occur often since
                    # we dont always upload a new watermark image every time the local datastore is cleared.
                    # Therefore, in debugging mode surpress this error message.
                    error_reporting.log_exception(logging.error, error_message = 'Watermark image not found!!')
                    
                composite_image = uploaded_photo   
                    
                
                    
            orig_img.resize(MEDIUM_IMAGE_X, MEDIUM_IMAGE_Y)
            photo.medium_before_watermark = orig_img.execute_transforms(output_encoding=images.PNG)
                    
            photo.large = composite_image

            img = images.Image(composite_image)
            img.resize(MEDIUM_IMAGE_X, MEDIUM_IMAGE_Y)
            photo.medium = img.execute_transforms(output_encoding=images.PNG)            
                        
            img.resize(SMALL_IMAGE_X,SMALL_IMAGE_Y)
            photo.small = img.execute_transforms(output_encoding=images.PNG)
               
        # Eventually, we can put more specific exception catching here -- but for now,
        # I don't even know which exceptions are being generated by the image transform
        # functions.
        except:
            error_reporting.log_exception(logging.error, error_message = 'resize_and_put_photos exception')
        else: # no exception occured
            photo.parent_object = userobject.key
            photo.is_private = False
            photo.has_been_reviewed = False 
            if num_photos == 0:
                # mark photo as profile photo if they don't have one
                photo.is_profile = True
                
            utils.put_object(photo)
            
            # The following writing of unique_last_login_offset_ref is necessary here in-case the user doesn't 
            # click on the "save changes" button, which is where we also set these values. Note, if this is not 
            # written (either here or in store_photo_options), then the users photos will not be displayed when 
            # someone views their profile.
            unique_last_login_offset_obj = userobject.unique_last_login_offset_ref.get()
            unique_last_login_offset_obj.has_public_photo_offset = True
            unique_last_login_offset_obj.has_profile_photo_offset = True
            unique_last_login_offset_obj.put()

    else:
        # silently fail if they try to upload more photos -- they will easily see that the photo
        # limit has been reached. (could put a logging.info('warning ... ') - but this doesn' seem necessary)
        pass
        
    # Return a re-direct to the photos for edit -- this also sends back a status 302 which
    # is (for some reason) required by app engine - sending a code 200 would generate warnings.
    return HttpResponseRedirect('/rs/ajax/load_photos_for_edit/')
    
#############################################

def get_uploads(request, field_name=None, populate_post=False):
    """Get uploads sent to this handler.
    Args:
      field_name: Only select uploads that were sent as a specific field.
      populate_post: Add the non blob fields to request.POST
    Returns:
      A list of BlobInfo records corresponding to each upload.
      Empty list if there are no blob-info records for field_name.
    """
    
    if hasattr(request,'__uploads') == False:
        fields = cgi.FieldStorage(request.META['wsgi.input'], environ=request.META)
        
        request.__uploads = {}
        if populate_post:
            request.POST = {}
        
        for key in fields.keys():
            field = fields[key]
            if isinstance(field, cgi.FieldStorage) and 'blob-key' in field.type_options:
                request.__uploads.setdefault(key, []).append(blobstore.parse_blob_info(field))
            elif populate_post:
                request.POST[key] = field.value
    if field_name:
        try:
            return list(request.__uploads[field_name])
        except KeyError:
            return []
    else:
        results = []
        for uploads in request.__uploads.itervalues():
            results += uploads
        return results



def blobstore_photo_upload(request):
    
    
    try:
        if request.method != 'POST':
            return HttpResponseBadRequest()
         
        else:
            userobject = utils_top_level.get_userobject_from_request(request)
            # make sure that the userobject is set.
            assert(userobject)
    
                
        blob_info_list = get_uploads(request)
        blob_info = blob_info_list[0]
        
        if WRITE_WATERMARK_HACK:
            if userobject.username == constants.ADMIN_USERNAME:
                return_val = write_watermark_to_dabase(userobject, blob_info)
            else:
                error_reporting.log_exception(logging.error, error_message = 'Enabled hack - Writing new watermark to database')
                return_val = resize_and_put_photos(userobject, blob_info) 
        else:
            return_val = resize_and_put_photos(userobject, blob_info)          
            
        # clear the value from the blobstore, as we no longer need (or want) to keep the original 
        # photo. 
        blob_info.delete()
        return return_val
    except:
        error_reporting.log_exception(logging.error, error_message = 'blobstore_photo_upload exception')
        return HttpResponseRedirect('/rs/ajax/load_photos_for_edit/')        