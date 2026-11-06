/* GPL-3.0-or-later. Resident field-menu hooks; no scene/save ownership. */
#ifndef SGP_FIELDBOOK_H
#define SGP_FIELDBOOK_H
void fieldbook_create(void *menu);
void fieldbook_frame(void *task, void *menu);
int fieldbook_touch(void *menu);
void fieldbook_dpad(void *menu);
void fieldbook_focus(void **sprites, unsigned index);
int fieldbook_task_input(void *task_manager);
int fieldbook_launch(void *task_manager);
int fieldbook_return(void *task_manager);
#endif
