// DATASETS Configuration
// Data source: Genrobot's 10Kh-RealOmin-OpenData (https://huggingface.co/datasets/genrobot2025/10Kh-RealOmin-OpenData)
// DAIMON data now available for WBCD 2026 competition

export const DATASETS = [
  {
    id: 'genrobot-1',
    name: 'Clean Bowl',
    source: 'Genrobot',
    description: 'Bimanual bowl cleaning task demonstrating coordinated manipulation',
    thumbnail: './thumbnails/clean_bowl.jpg',
    rrdUrl: './rrd/clean_bowl.rrd',
    topics: {
      transforms: ['/robot0/vio/eef_pose', '/robot1/vio/eef_pose'],
      cameras: ['/robot0/sensor/camera0', '/robot1/sensor/camera0'],
    },
  },
  {
    id: 'genrobot-2',
    name: 'Unscrew Bottle Cap and Pour',
    source: 'Genrobot',
    description: 'Fine manipulation task: unscrewing cap and pouring liquid',
    thumbnail: './thumbnails/unscrew_bottle_cap_and_pour.jpg',
    rrdUrl: './rrd/unscrew_bottle_cap_and_pour.rrd',
    topics: {
      transforms: ['/robot0/vio/eef_pose', '/robot1/vio/eef_pose'],
      cameras: ['/robot0/sensor/camera0', '/robot1/sensor/camera0'],
    },
  },
  {
    id: 'dm-insert-1',
    name: 'Memory Cube Insert',
    source: 'DAIMON',
    description: 'Precision insertion task with 8-DOF arm and tactile sensing (DM Robotics)',
    thumbnail: './thumbnails/dm_insert_episode_0.jpg',
    rrdUrl: './rrd/dm_insert_episode_0.rrd',
    topics: {
      cameras: ['/cameras/top', '/cameras/wrist', '/cameras/tactile'],
      scalars: ['/observation/state', '/action'],
    },
  },
  {
    id: 'dm-tacexo-1',
    name: 'Fold Towels (TacExo)',
    source: 'DAIMON',
    description: 'Bimanual glove manipulation with thumb tactile sensing (TacExo)',
    thumbnail: './thumbnails/tacexo_fold_towels_episode_0.jpg',
    rrdUrl: './rrd/tacexo_fold_towels_episode_0.rrd',
    topics: {
      cameras: ['/cameras/third_view', '/tactile/left_thumb', '/tactile/right_thumb'],
      scalars: ['/fingers'],
    },
  },
  {
    id: 'lumos-task-1',
    name: 'Object Packing: Light Bulb',
    source: 'Lumos',
    description: 'Bimanual manipulation task of packing a single light bulb into a small box',
    thumbnail: './thumbnails/lumos_task1.jpg',
    rrdUrl: './rrd/lumos_task1.rrd',
    topics: {
      transforms: ['world/left_hand/eef', 'world/right_hand/eef'],
      cameras: ['world/left_hand/camera', 'world/right_hand/camera'],
    },
  },
  {
    id: 'lumos-task-2',
    name: 'Object Packing: Cups',
    source: 'Lumos',
    description: 'Pack 2 water cups into a large box',
    thumbnail: './thumbnails/lumos_task2.jpg',
    rrdUrl: './rrd/lumos_task2.rrd',
    topics: {
      transforms: ['world/left_hand/eef', 'world/right_hand/eef'],
      cameras: ['world/left_hand/camera', 'world/right_hand/camera'],
    },
  },
];

// Data source information
export const DATA_SOURCE = {
  name: 'Genrobot 10Kh-RealOmin-OpenData',
  url: 'https://huggingface.co/datasets/genrobot2025/10Kh-RealOmin-OpenData',
  note: 'Featuring data from Genrobot, DAIMON and Lumos for WBCD 2026 competition.',
};
