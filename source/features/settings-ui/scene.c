/* Private role glue in the one dynamic Scene translation unit. */
#include "../ui-native/scene.h"
static unsigned settings_scene_capture(SettingsApp *a) {
 SettingsSnapshot snapshot;
 unsigned s=settings_owner_capture(a,&a->owners,&snapshot);
 if(s==SGP_SHINY_OK) {
  settings_init(&a->model,&snapshot);a->preview_origin=~0u;
  a->preview_speed=~0u;a->common.preview_units=~0u;
 }
 return s;
}
static unsigned settings_scene_build(SettingsApp *a,unsigned epoch) {
 SceneCommon *c=&a->common;
 SettingsRenderRequest r={&a->model,&a->catalog,&a->desired,sizeof(a->desired),
  c->pool,256,epoch,a->first,a->selector_first,c->preview_units};
 if(!settings_render_build(&r))return 0;
 a->first=a->desired.first;return 1;
}
/* One invocation per positively fresh normal Main boundary, not per font call.
 * Delays are the pinned native Options_GetTextFrameDelay logical0/1/2 mapping.
 * Immutable plans/pools are rebuilt only by the common visible-idle barrier. */
static void settings_scene_tick(SettingsApp *a,unsigned fresh) {
 SceneCommon *c=&a->common;unsigned speed=a->model.draft.native.text;
 if(a->model.view!=SETTINGS_INFO) {
  a->preview_origin=~0u;c->preview_units=~0u;c->preview_frames=0;return;
 }
 if(a->preview_origin!=a->model.info_origin || a->preview_speed!=speed) {
  a->preview_origin=a->model.info_origin;a->preview_speed=speed;
  c->preview_units=0;c->preview_frames=0;c->preview_due=1;return;
 }
 if(!fresh || c->suspended || c->bg.front>=2)return;
 const SettingsPaintHistory *front=&a->painter.history[c->bg.front];
 if(!front->valid || front->version!=c->bg.version[c->bg.front] ||
 front->plan.view!=SETTINGS_INFO)return;
 unsigned delay=speed==0?8:speed==1?4:1;
 if(++c->preview_frames>=delay) {
  c->preview_frames=0;
  UiResourceSlice s;
  if(ui_res_text(&c->chrome,SGP_UI_PREVIEW_TEXT,&s) && c->preview_units<s.bytes/2-1) {
   ++c->preview_units;c->preview_due=1;
  }
 }
}
static SettingsResult settings_scene_input(SettingsApp *a,unsigned fresh,unsigned busy,
 unsigned mapped,unsigned repeated,unsigned mode) {
 SceneCommon *c=&a->common;
 settings_sample(&a->model,c->sample.held,fresh==PHYS_FRESH,fresh==PHYS_SUSPEND);
 unsigned keys=0,repeat=0;
 if(fresh==PHYS_FRESH && !busy && !(c->sample.flags&PHYS_RELEASE_ONLY)) {
  keys=settings_keys(mapped,c->sample.pressed,mode);
  repeat=settings_keys(repeated,c->sample.repeated,mode);
 }
 return settings_step(&a->model,keys,repeat);
}
