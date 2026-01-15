// DATASETS Configuration
// Data source: Genrobot's 10Kh-RealOmin-OpenData (https://huggingface.co/datasets/genrobot2025/10Kh-RealOmin-OpenData)
// DM Robot and Lumos data coming soon for WBCD 2026 competition

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
    id: 'genrobot-3',
    name: 'Zip Clothes',
    source: 'Genrobot',
    description: 'Precision zipping task with deformable garment handling',
    thumbnail: './thumbnails/zip_clothes.jpg',
    rrdUrl: './rrd/zip_clothes.rrd',
    topics: {
      transforms: ['/robot0/vio/eef_pose', '/robot1/vio/eef_pose'],
      cameras: ['/robot0/sensor/camera0', '/robot1/sensor/camera0'],
    },
  },
];

// Data source information
export const DATA_SOURCE = {
  name: 'Genrobot 10Kh-RealOmin-OpenData',
  url: 'https://huggingface.co/datasets/genrobot2025/10Kh-RealOmin-OpenData',
  note: 'Additional data from DM Robot and Lumos coming soon for WBCD 2026 competition.',
};
