/*
 * GStreamer
 * Copyright (C) 2018-2020 RidgeRun <support@ridgerun.com>
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Library General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Library General Public License for more details.
 *
 * You should have received a copy of the GNU Library General Public
 * License along with this library; if not, write to the
 * Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 *
 */

/*
 * This is the modified version of RidgeRun code
 * (https://github.com/RidgeRun/gst-inference) to support Xilinx VVAS product
 * specific use cases
 */

#include "gstinferenceclassification.h"

#include <string.h>

#define DEFAULT_CLASS_ID -1
#define DEFAULT_CLASS_PROB 0.0f
#define DEFAULT_CLASS_LABEL NULL
#define DEFAULT_NUM_CLASSES 0
#define DEFAULT_PROBABILITIES NULL
#define DEFAULT_LABELS NULL

static GType gst_inference_classification_get_type (void);
GST_DEFINE_MINI_OBJECT_TYPE (GstInferenceClassification,
    gst_inference_classification);

static void classification_free (GstInferenceClassification * self);
static void classification_reset (GstInferenceClassification * self);

static gdouble *probabilities_copy (const gdouble * from, gint num_classes);

static guint64 get_new_id (void);

static guint64
get_new_id (void)
{
  static guint64 _id = G_GUINT64_CONSTANT (0);
  static GMutex _id_mutex;
  static guint64 ret = 0;

  g_mutex_lock (&_id_mutex);
  ret = _id++;
  g_mutex_unlock (&_id_mutex);

  return ret;
}

static void
classification_reset (GstInferenceClassification * self)
{
  g_return_if_fail (self);

  self->classification_id = get_new_id ();
  self->class_id = DEFAULT_CLASS_ID;
  self->class_prob = DEFAULT_CLASS_PROB;
  self->num_classes = DEFAULT_NUM_CLASSES;
  self->label_color.red = 0;
  self->label_color.green = 0;
  self->label_color.blue = 0;
  self->label_color.alpha = 0;

  if (self->class_label) {
    g_free (self->class_label);
  }
  self->class_label = DEFAULT_CLASS_LABEL;

  if (self->probabilities) {
    g_free (self->probabilities);
  }
  self->probabilities = DEFAULT_PROBABILITIES;

  if (self->labels) {
    g_strfreev (self->labels);
  }
  self->labels = DEFAULT_LABELS;
}

GstInferenceClassification *
gst_inference_classification_new (void)
{
  GstInferenceClassification *self = g_slice_new (GstInferenceClassification);

  gst_mini_object_init (GST_MINI_OBJECT_CAST (self), 0,
      gst_inference_classification_get_type (),
      (GstMiniObjectCopyFunction) gst_inference_classification_copy, NULL,
      (GstMiniObjectFreeFunction) classification_free);

  g_mutex_init (&self->mutex);

  self->class_label = NULL;
  self->probabilities = NULL;
  self->labels = NULL;

  classification_reset (self);

  return self;
}

static gdouble *
probabilities_copy (const gdouble * from, gint num_classes)
{
  gsize size = 0;
  gdouble *to = NULL;

  g_return_val_if_fail (from, NULL);
  g_return_val_if_fail (num_classes > 0, NULL);

  size = num_classes * sizeof (double);
  to = g_malloc0 (size);

  memcpy (to, from, size);

  return to;
}

GstInferenceClassification *
gst_inference_classification_new_full (gint class_id, gdouble class_prob,
    const gchar * class_label, gint num_classes, const gdouble * probabilities,
    gchar ** labels, VvasColorMetadata *label_color)
{
  GstInferenceClassification *self = gst_inference_classification_new ();

  GST_INFERENCE_CLASSIFICATION_LOCK (self);

  self->class_id = class_id;
  self->class_prob = class_prob;
  self->num_classes = num_classes;

  if (class_label) {
    self->class_label = g_strdup (class_label);
  }

  if (probabilities && num_classes > 0) {
    self->probabilities = probabilities_copy (probabilities, num_classes);
  }

  if (labels) {
    self->labels = g_strdupv (labels);
  }

  if (label_color) {
    self->label_color.red = label_color->red;
    self->label_color.green = label_color->green;
    self->label_color.blue = label_color->blue;
    self->label_color.alpha = label_color->alpha;
  }

  GST_INFERENCE_CLASSIFICATION_UNLOCK (self);

  return self;
}

GstInferenceClassification *
gst_inference_classification_ref (GstInferenceClassification * self)
{
  g_return_val_if_fail (self, NULL);

  return (GstInferenceClassification *)
      gst_mini_object_ref (GST_MINI_OBJECT_CAST (self));
}

void
gst_inference_classification_unref (GstInferenceClassification * self)
{
  g_return_if_fail (self);

  gst_mini_object_unref (GST_MINI_OBJECT_CAST (self));
}

GstInferenceClassification *
gst_inference_classification_copy (const GstInferenceClassification * self)
{
  GstInferenceClassification *other = NULL;

  g_return_val_if_fail (self, NULL);

  other = gst_inference_classification_new ();

  GST_INFERENCE_CLASSIFICATION_LOCK ((GstInferenceClassification *) self);

  other->classification_id = self->classification_id;
  other->class_id = self->class_id;
  other->class_prob = self->class_prob;
  other->num_classes = self->num_classes;
  other->label_color.red = self->label_color.red;
  other->label_color.green = self->label_color.green;
  other->label_color.blue = self->label_color.blue;
  other->label_color.alpha = self->label_color.alpha;

  if (self->class_label) {
    other->class_label = g_strdup (self->class_label);
  }

  if (self->probabilities) {
    other->probabilities =
        probabilities_copy (self->probabilities, self->num_classes);
  }

  if (self->labels) {
    other->labels = g_strdupv (self->labels);
  }

  GST_INFERENCE_CLASSIFICATION_UNLOCK ((GstInferenceClassification *) self);

  return other;
}

gchar *
gst_inference_classification_to_string (GstInferenceClassification * self,
    gint level)
{
  gint indent = level * 2;
  gchar *serial = NULL;

  g_return_val_if_fail (self, NULL);

  GST_INFERENCE_CLASSIFICATION_LOCK (self);

  serial = g_strdup_printf ("{\n"
      "%*s  Id : %" G_GUINT64_FORMAT "\n"
      "%*s  Class : %d\n"
      "%*s  Label : %s\n"
      "%*s  Probability : %f\n"
      "%*s  Classes : %d\n"
      "%*s}",
      indent, "", self->classification_id,
      indent, "", self->class_id,
      indent, "", self->class_label,
      indent, "", self->class_prob, indent, "", self->num_classes, indent, "");

  GST_INFERENCE_CLASSIFICATION_UNLOCK (self);

  return serial;
}

static void
classification_free (GstInferenceClassification * self)
{
  classification_reset (self);

  g_mutex_clear (&self->mutex);
  g_slice_free(GstInferenceClassification, self);
}
