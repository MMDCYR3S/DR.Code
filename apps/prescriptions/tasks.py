# apps/prescriptions/tasks.py

import logging
from celery import shared_task
from PIL import Image
import os
import gc

logger = logging.getLogger('image_compression')
Image.MAX_IMAGE_PIXELS = None


@shared_task(
    bind=True,
    max_retries=0,
    time_limit=180,
    soft_time_limit=150
)
def compress_prescription_image(self, image_id):
    """فشرده‌سازی هوشمند با مدیریت حافظه"""
    
    logger.info(f"START Task {image_id} (PID: {os.getpid()})")
    
    try:
        from apps.prescriptions.models import PrescriptionImage
        
        image_obj = PrescriptionImage.objects.get(id=image_id)
        
        if image_obj.is_compressed:
            logger.info(f"Already compressed: {image_id}")
            return "Already compressed"
        
        image_path = image_obj.image.path
        
        if not os.path.exists(image_path):
            logger.error(f"File not found: {image_path}")
            return "File not found"
        
        original_size = os.path.getsize(image_path) / (1024 * 1024)
        logger.info(f"Original: {original_size:.2f}MB, Path: {image_path}")
        
        # فشرده‌سازی بر اساس سایز فایل
        if original_size > 100:
            # خیلی سنگین → حالت اضطراری
            success = emergency_compress(image_path, image_id)
        elif original_size > 10:
            # سنگین → فشرده‌سازی شدید
            success = heavy_compress(image_path, image_id)
        else:
            # معمولی → فشرده‌سازی استاندارد
            success = standard_compress(image_path, image_id)
        
        if success:
            image_obj.is_compressed = True
            image_obj.save(update_fields=['is_compressed'])
            
            final_size = os.path.getsize(image_path) / (1024 * 1024)
            reduction = ((original_size - final_size) / original_size) * 100
            
            logger.info(f"DONE {image_id}: {original_size:.1f}MB → {final_size:.1f}MB (-{reduction:.0f}%)")
            return f"Compressed: -{reduction:.0f}%"
        else:
            logger.error(f"Compression failed: {image_id}")
            return "Compression failed"
            
    except Exception as e:
        logger.error(f"ERROR {image_id}: {e}", exc_info=True)
        return f"Failed: {e}"
    
    finally:
        gc.collect()


def emergency_compress(image_path, image_id):
    """
    حالت اضطراری برای تصاویر خیلی سنگین (>100MB)
    بدون لود کامل فایل در حافظه
    """
    temp_path = None
    
    try:
        logger.warning(f"EMERGENCY MODE for {image_id}")
        
        # باز کردن فایل بدون لود کامل
        with Image.open(image_path) as img:
            
            # محاسبه ابعاد جدید بدون لود تصویر
            original_width, original_height = img.size
            logger.info(f"Original size: {original_width}x{original_height}")
            
            # محاسبه RAM مورد نیاز (تخمینی)
            estimated_ram_mb = (original_width * original_height * 3) / (1024 * 1024)
            logger.warning(f"Estimated RAM needed: {estimated_ram_mb:.1f}MB")
            
            # اگر بیش از 300MB RAM لازم داره، ابعاد رو خیلی کم کن
            if estimated_ram_mb > 300:
                # کاهش به 1/8 سایز اصلی
                scale_factor = 8
                draft_size = (original_width // scale_factor, original_height // scale_factor)
                logger.warning(f"Scale down to 1/{scale_factor}: {draft_size}")
            else:
                # کاهش به 1/4 سایز اصلی
                scale_factor = 4
                draft_size = (original_width // scale_factor, original_height // scale_factor)
            
            # استفاده از draft برای کاهش حافظه
            try:
                img.draft('RGB', draft_size)
                logger.info(f"Draft mode applied: {draft_size}")
            except Exception as e:
                logger.warning(f"Draft failed: {e}")
            
            # تبدیل به RGB
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            
            # Resize به سایز نهایی خیلی کوچک
            img.thumbnail((800, 800), Image.Resampling.LANCZOS)
            logger.info(f"Thumbnail size: {img.size}")
            
            # ذخیره با کیفیت پایین
            temp_path = image_path + '.emergency.jpg'
            img.save(
                temp_path,
                'JPEG',
                quality=60,
                optimize=True,
                progressive=True
            )
        
        gc.collect()
        logger.info("Image object closed, memory freed")
        
        # جایگزینی فایل اصلی
        if os.path.exists(temp_path):
            os.replace(temp_path, image_path)
            logger.warning("Emergency compression applied (800x800, quality=60)")
            return True
        
        return False
        
    except MemoryError:
        logger.error("MemoryError even in emergency mode!")
        return False
        
    except Exception as e:
        logger.error(f"Emergency compress failed: {e}", exc_info=True)
        return False
    
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        gc.collect()


def heavy_compress(image_path, image_id):
    """فشرده‌سازی شدید برای تصاویر سنگین (10-100MB)"""
    temp_path = None
    
    try:
        logger.info(f"HEAVY MODE for {image_id}")
        
        with Image.open(image_path) as img:
            
            original_width, original_height = img.size
            estimated_ram_mb = (original_width * original_height * 3) / (1024 * 1024)
            logger.info(f"Size: {original_width}x{original_height}, RAM: {estimated_ram_mb:.1f}MB")
            
            # Draft mode برای کاهش حافظه
            try:
                img.draft('RGB', (2048, 2048))
            except:
                pass
            
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            
            # Resize به 1280x1280
            img.thumbnail((1280, 1280), Image.Resampling.LANCZOS)
            logger.info(f"Resized to: {img.size}")
            
            temp_path = image_path + '.heavy.jpg'
            img.save(
                temp_path,
                'JPEG',
                quality=70,
                optimize=True,
                progressive=True
            )
        
        gc.collect()
        
        if os.path.exists(temp_path):
            os.replace(temp_path, image_path)
            logger.info("Heavy compression applied (1280x1280, quality=70)")
            return True
        
        return False
        
    except MemoryError:
        logger.error("MemoryError in heavy mode, switching to emergency")
        return emergency_compress(image_path, image_id)
        
    except Exception as e:
        logger.error(f"Heavy compress failed: {e}", exc_info=True)
        return False
    
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        gc.collect()


def standard_compress(image_path, image_id):
    """فشرده‌سازی استاندارد برای تصاویر معمولی (<10MB)"""
    temp_path = None
    
    try:
        logger.info(f"STANDARD MODE for {image_id}")
        
        with Image.open(image_path) as img:
            
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            
            aspect_ratio = img.width / img.height
            
            if aspect_ratio > 1.5:
                target_size = (1600, 900)
            elif aspect_ratio < 0.8:
                target_size = (900, 1600)
            else:
                target_size = (1280, 1280)
            
            img.thumbnail(target_size, Image.Resampling.LANCZOS)
            logger.info(f"Resized to: {img.size}")
            
            temp_path = image_path + '.standard.jpg'
            img.save(
                temp_path,
                'JPEG',
                quality=75,
                optimize=True,
                progressive=True
            )
        
        gc.collect()
        
        if os.path.exists(temp_path):
            os.replace(temp_path, image_path)
            logger.info("Standard compression applied")
            return True
        
        return False
        
    except MemoryError:
        logger.error("MemoryError in standard mode, switching to heavy")
        return heavy_compress(image_path, image_id)
        
    except Exception as e:
        logger.error(f"Standard compress failed: {e}", exc_info=True)
        return False
    
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        gc.collect()
