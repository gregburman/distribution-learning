SETUP_DIR=$1

nvidia-docker run -v /home/greg/git/distribution-learning:/distribution-learning greggoburman/distribution-learning:gp-v1 python train/prob_unet/$SETUP_DIR/mknet_train.py $SETUP_DIR
