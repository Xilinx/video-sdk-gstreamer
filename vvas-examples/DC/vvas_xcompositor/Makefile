$CC := gcc

GST_INC_PATH ?= /usr/local/include/gstreamer-1.0
GST_LIB_PATH ?= /usr/lib/gstreamer-1.0

OBJS += \
./vvas_xcompositor.o

OUTPUT = vvas_xcompositor

CFLAGS +=  -Wall -O0 -g3
CFLAGS += -I/usr/include/
CFLAGS += `pkg-config  --cflags glib-2.0`
CFLAGS += `pkg-config --cflags gstreamer-1.0`

LFLAGS += -L=/lib -L=/usr/lib
LFLAGS += `pkg-config --libs glib-2.0`
LFLAGS += `pkg-config --libs gstreamer-1.0`


LIBS := -lgstpbutils-1.0

# All Target
all: $(OUTPUT)

%.o: ./src/%.c
	@echo 'Building file: $<'
	@echo 'Invoking: ${CC} Linux gcc compiler'
	$(CC) -c -o $@ $< $(CFLAGS)
	@echo 'Finished building: $<'
	@echo ' '


# Tool invocations
$(OUTPUT): $(OBJS)  $(USER_OBJS)
	@echo 'Building target: $@'
	@echo 'Invoking: ${CC} Linux gcc linker'
	$(CC) -o $@ $^ $(LFLAGS) $(LIBS)
	-$(RM) $(OBJS)
	@echo 'Finished building target: $@'
	@echo ' '

# Other Targets
clean:
	-$(RM) $(OBJS) $(OUTPUT)
	-@echo ' '

.PHONY: all clean
