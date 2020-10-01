#!/usr/bin/python3

import btrfs
import sys
import time

def disk_full(size,allocated):
  limit1 = size * .8
  limit2 = size - 2147483648
  limit = max(limit1,limit2)
  if allocated > limit:
    return True
  else:
    return False

def data_empty(size,data_free_space):
  chunk= min(size *.1,1073741824)
  if data_free_space > chunk:
    return True
  else:
    return False

def balance_needed(fs):
  usage=fs.usage()
  total=usage.total
  allocated=usage.allocated
  if not disk_full(total,allocated):
    return False
  alldata=usage.virtual_space_usage
  for _,data_type in alldata.items():
    if data_type.flags & btrfs.BLOCK_GROUP_DATA:
      data_total=data_type.total
      data_used=data_type.used
      return data_empty(total,data_total-data_used)
  else:
    raise NameError("Couldn't find DATA blocks!")

def analyze_block_groups(fs):
    min_size=14000000000000000000
    min_size_block=None
    max_size=-1
    free_space=-1
    for chunk in fs.chunks():
        if not (chunk.type & btrfs.BLOCK_GROUP_DATA):
            continue
        try:
            block_group = fs.block_group(chunk.vaddr, chunk.length)
            #print(block_group)
            if block_group.used < min_size:
                if min_size_block != None:
                    free_space=min_size_block.length-min_size_block.used
                min_size=block_group.used
                #print(min_size_block)
                min_size_block=block_group
            if block_group.used > max_size:
                max_size_size=block_group.used
        except IndexError:
            continue
    if min_size == max_size or min_size_block.used >= free_space:
        return None
    #print(min_size_block,free_space)
    return min_size_block

def balance_block_group(fs,block_group):
    vaddr = block_group.vaddr
    args = btrfs.ioctl.BalanceArgs(vstart=block_group.vaddr, vend=block_group.vaddr+1)
    print("Balance block group vaddr {} used_pct {} ...".format(block_group.vaddr, block_group.used_pct), end='', flush=True)
    start_time = time.time()
    try:
        progress = btrfs.ioctl.balance_v2(fs.fd, data_args=args)
        end_time = time.time()
        print(" duration {} sec total {}".format(int(end_time - start_time), progress.considered))
    except KeyboardInterrupt:
        end_time = time.time()
        print(" duration {} sec".format(int(end_time - start_time)))
        raise

def main():
    fs= btrfs.FileSystem(sys.argv[1])
    while balance_needed(fs):
      min_size_block = analyze_block_groups(fs)
      if min_size_block != None:
        balance_block_group(fs,min_size_block)
      else:
        raise NameError("Balance wants to run, but no data will be moved!")
    else:
      print("No balance is needed")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: {} <mountpoint>".format(sys.argv[0]))
        sys.exit(1)
    try:
        main()
    except KeyboardInterrupt:
        print("Exiting...")
        sys.exit(130)  # 128 + SIGINT
    except Exception as e:
        print(e)
        sys.exit(1)
